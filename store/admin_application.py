import json

from flask import Flask, Response
from flask_jwt_extended import JWTManager

from configuration import Configuration
from models import database, Product, Category, ProductCategory, OrderedProduct
from roleCheck import role_check

from sqlalchemy import func, desc

application = Flask(__name__)
application.config.from_object(Configuration)
jwt = JWTManager(application)


@application.route('/productStatistics', methods=["GET"])
@role_check("admin")
def product_statistics():
    query_result = Product.query.join(OrderedProduct).group_by(Product.name). \
        with_entities(Product.name, func.sum(OrderedProduct.requested_quantity).label("sold"),
                      func.sum(OrderedProduct.requested_quantity - OrderedProduct.received_quantity).label("waiting"))

    statistics = [{
        "name": product.name,
        "sold": int(product.sold),
        "waiting": int(product.waiting)
    } for product in query_result]

    return Response(json.dumps({"statistics": statistics}), status=200)


@application.route('/categoryStatistics', methods=["GET"])
@role_check("admin")
def category_statistics():
    query_result = Category.query.outerjoin(ProductCategory) \
        .outerjoin(OrderedProduct, OrderedProduct.product_id == ProductCategory.product_id) \
        .group_by(Category.name) \
        .order_by(func.sum(OrderedProduct.requested_quantity).desc(), Category.name) \
        .with_entities(Category.name) \
        .all()

    # outer join se koristi jer treba da se racunaju i oni proizvodi koji nisu bili u porudzbini

    statistics = [category.name for category in query_result]

    return Response(json.dumps({"statistics": statistics}), status=200)


if __name__ == '__main__':
    database.init_app(application)
    application.run(debug=True, host='0.0.0.0', port=5003)
