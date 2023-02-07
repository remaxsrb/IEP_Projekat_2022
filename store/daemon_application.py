import collections

from flask import Flask
from redis import Redis

from sqlalchemy import and_

from configuration import Configuration
from models import database
from models import Product, Category, ProductCategory, OrderedProduct, Order

import json

application = Flask(__name__)
application.config.from_object(Configuration)


# radi lakseg proveravanja kategorija
def check_categories(categories1, categories2):
    for curr_category in categories1:
        if curr_category not in categories2:
            return False

    return True


if __name__ == "__main__":

    database.init_app(application)
    while True:
        with Redis(host=Configuration.REDIS_HOST) as redis:

            with application.app_context() as context:

                incoming_product = json.loads(redis.blpop(Configuration.REDIS_WAREHOUSE_QUEUE)[1])

                incoming_product_categories = incoming_product["product_categories"].split("|")
                incoming_product_name = incoming_product["product_name"]
                product_delivery_quantity = int(incoming_product["product_amount"])
                product_delivery_price = float(incoming_product["product_price"])

                existing_product = Product.query.filter(Product.name == incoming_product_name).first()

                if existing_product is None:

                    # nema proizvoda u bazi, ubacuje se i proveravaju se kategorije

                    new_product = Product(name=incoming_product_name, price=product_delivery_price,
                                          stock=product_delivery_quantity)
                    database.session.add(new_product)
                    database.session.commit()

                    for product_category in incoming_product_categories:

                        existing_category = Category.query.filter(Category.name == product_category).first()

                        if existing_category is None:
                            # ne postoji kategorija te se dodaje

                            new_category = Category(name=product_category)
                            database.session.add(new_category)
                            database.session.commit()

                            product_category_relationship = ProductCategory(product_id=new_product.id,
                                                                            category_id=new_category.id)
                            database.session.add(product_category_relationship)
                            database.session.commit()

                        else:
                            product_category_relationship = ProductCategory(product_id=new_product.id,
                                                                            category_id=existing_category.id)
                            database.session.add(product_category_relationship)
                            database.session.commit()

                else:
                    # proizvod postoji
                    existing_product_categories = [category.name for category in existing_product.categories]

                    print(f"existing_product_categories: {existing_product_categories}", flush=True)
                    print(f"incoming_product_categories: {incoming_product_categories}", flush=True)

                    if check_categories(incoming_product_categories, existing_product_categories):

                        new_price = ((existing_product.stock * existing_product.price + product_delivery_quantity *
                                      product_delivery_price) / (
                                             existing_product.stock + product_delivery_quantity))

                        existing_product.price = new_price
                        existing_product.stock += product_delivery_quantity

                        database.session.commit()

                        potential_waiting_orders = database.session.query(OrderedProduct).join(Order).filter(and_(
                            OrderedProduct.product_id == existing_product.id,
                            OrderedProduct.received_quantity < OrderedProduct.requested_quantity
                        )).order_by(Order.timestamp).all()

                        for ordered_product in potential_waiting_orders:

                            if existing_product.stock >= ordered_product.requested_quantity:

                                needed_quantity = ordered_product.requested_quantity - ordered_product.recieved_quantity
                                provided_quantity = needed_quantity if needed_quantity < existing_product.stock \
                                    else existing_product.stock

                                existing_product.stock -= provided_quantity
                                ordered_product.recieved_quantity += provided_quantity

                                database.session.commit()

                                completed_order = database.session.query(OrderedProduct).filter(and_(
                                    OrderedProduct.order_id == ordered_product.order_id,
                                    OrderedProduct.received_quantity == OrderedProduct.requested_quantity
                                )).first()

                                if completed_order is not None:
                                    order = Order.query.filter(Order.id == ordered_product.order_id).first()
                                    order.status = "COMPLETE"
                                    database.session.commit()

                                else:
                                    ordered_product.recieved_quantity += provided_quantity
                                    existing_product.stock = 0
                                    database.session.commit()
