from redis import Redis
from sqlalchemy import and_

from configuration import Configuration
from models import database
from models import Product, Category, ProductCategory, OrderedProducts, Order

import sys
import threading
import json
import logging

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def check_products():
    with Redis(host=Configuration.REDIS_HOST) as redis:

        subscription = redis.pubsub()
        subscription.subscribe(Configuration.REDIS_WAREHOUSE_QUEUE)

        for message in subscription.listen():

            if message['type'] == 'message':
                logging.debug(message)

                data = json.loads(message['data'])

                logging.debug(data)

                product_categories = data.get('product_categories')
                incoming_product_categories_list = product_categories.split("|")
                product_name = data.get('product_name')
                product_delivery_quantity = data.get('product_amount')
                product_delivery_price = data.get('product_price')

                existing_products_db = database.session.query(Product.name).all()
                existing_categories_db = database.session.query(Category.name).all()
                database.session.close()

                if product_name not in existing_products_db:
                    product = Product(name=product_name, price=product_delivery_price, stock=product_delivery_quantity)
                    database.session.add(product)
                    database.session.commit()

                    for product_category in incoming_product_categories_list:
                        category = Category(product_category)
                        database.session.add(category)
                        database.session.commit()

                        product_category_rel = ProductCategory(productId=product.id, categoryId=category.id)
                        database.session.add(product_category_rel)
                        database.session.commit()
                else:

                    existing_categories_db.sort()
                    incoming_product_categories_list.sort()

                    if existing_categories_db == incoming_product_categories_list:

                        product = Product.query.filter(Product.name == product_name).first()

                        current_product_price = database.session.query(Product.price).filter_by(name=product_name).first()

                        current_product_stock = database.session.query(Product.stock).filter_by(name=product_name).first()

                        new_price = (current_product_stock * current_product_price + product_delivery_quantity *
                                     product_delivery_price) / (current_product_stock + product_delivery_quantity)

                        product.price = new_price
                        database.session.commit()

                        potential_orders = OrderedProducts.query().filter(and_(
                            OrderedProducts.productId == product.id,
                            OrderedProducts.received_quantity < OrderedProducts.requested_quantity
                        )).all()

                        for ordered_product in potential_orders:
                            needed_quantity = ordered_product.requested_quantity - ordered_product.recieved_quantity
                            provided_quantity = needed_quantity if needed_quantity < product.stock else product.stock
                            product.stock -= provided_quantity
                            ordered_product.recieved_quantity += provided_quantity

                            completed_order = OrderedProducts.query().filter(and_(
                                OrderedProducts.orderId == ordered_product.orderId,
                                OrderedProducts.received_quantity < OrderedProducts.requested_quantity
                            )).first()

                            if not completed_order:
                                order = Order.query.filter(Order.id == ordered_product.orderId).first()
                                order.status = True

                            database.session.commit()

                            if product.stock == 0:
                                break

                    else:
                        logging.debug(f'Existing and imported product categories are not matching')


t1 = threading.Thread(target=check_products)
t1.start()
