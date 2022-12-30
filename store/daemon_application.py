from redis import Redis
from sqlalchemy import and_

from configuration import Configuration
from database import Session
from models import Product, Category, ProductCategory, OrderedProducts, Order

import sys
import threading
import json
import logging

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
session = Session()


def checkProducts():
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

                existing_products_db = session.query(Product.name).all()
                existing_categories_db = session.query(Category.name).all()
                session.close()

                if product_name not in existing_products_db:
                    product = Product(name=product_name, price=product_delivery_price, stock=product_delivery_quantity)
                    session.add(product)
                    session.commit()

                    for product_category in incoming_product_categories_list:
                        category = Category(product_category)
                        session.add(category)
                        session.commit()

                        product_category_rel = ProductCategory(productId=product.id, categoryId=category.id)
                        session.add(product_category_rel)
                        session.commit()
                else:

                    existing_categories_db.sort()
                    incoming_product_categories_list.sort()

                    if existing_categories_db == incoming_product_categories_list:

                        product = Product.query.filter(Product.name == product_name).first()

                        current_product_price = session.query(Product.price).filter_by(name=product_name).first()

                        current_product_stock = session.query(Product.stock).filter_by(name=product_name).first()

                        new_price = (current_product_stock * current_product_price + product_delivery_quantity *
                                     product_delivery_price) / (current_product_stock + product_delivery_quantity)

                        product.price = new_price
                        session.commit()

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

                            session.commit()

                            if product.stock == 0:
                                break

                    else:
                        logging.debug(f'Existing and imported product categories are not matching')


t1 = threading.Thread(target=checkProducts)
t1.start()
