from redis import Redis
from configuration import Configuration
from database import Session
from models import Product, Category, ProductCategory

import sys
import threading
import json
import logging

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
session = Session()


def checkProducts():
    with Redis(host=Configuration.REDIS_HOST) as redis:

        subscription = redis.pubsub()
        subscription.subscribe(Configuration.REDIS_VOTE_QUEUE)

        for message in subscription.listen():

            if message['type'] == 'message':
                logging.debug(message)

                data = json.loads(message['data'])

                logging.debug(data)

                product_categories = data.get('product_categories')
                product_categories_list = product_categories.split("|")
                product_name = data.get('product_name')
                product_delivery_quantity = data.get('product_amount')
                product_delivery_price = data.get('product_price')

                existing_products = session.query(Product.name).all()
                existing_categories = session.query(Category.name).all()
                session.close()

                if product_name not in existing_products:
                    product = Product(name=product_name, price=product_delivery_price, stock=product_delivery_quantity)
                    session.add(product)
                    session.commit()

                    for product_category in product_categories_list:
                        category = Category(product_category)
                        session.add(category)
                        session.commit()

                        product_category_rel = ProductCategory(productId=product.id, categoryId=category.id)
                        session.add(product_category_rel)
                        session.commit()
                else:
                    existing_categories.sort()
                    product_categories_list.sort()

                    if existing_categories == product_categories_list:
                        product = session.query(Product.__tablename__).filter_by(name=product_name).first()

                    else:
                        logging.debug(f'Existing and imported product categories are not matching')


t1 = threading.Thread(target=checkProducts)
t1.start()

# product = Product(name=product_name, price=product_price, stock=product_amount)
# database.session.add(product)
# database.session.commit()
#
# for category in product_categories_list:
#     database.session.add(Category(name=category))
#     database.session.commit()
