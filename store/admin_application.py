from flask import Flask, jsonify
from flask_jwt_extended import JWTManager

from configuration import Configuration
from models import database, Product, Category, ProductCategory, OrderedProducts
from roleCheck import role_check

from sqlalchemy import func

application = Flask(__name__)
application.config.from_object(Configuration)
jwt = JWTManager(application)


@application.route('/productStatistics', methods=["GET"])
@role_check("admin")
def product_statistics():
    query_result = Product.query.join(OrderedProducts).group_by(Product.name).with_entities \
        (Product.name, func.sum(OrderedProducts.requested_quantity).label("sold"),
         func.sum(OrderedProducts.requested_quantity - OrderedProducts.received_quantity).label("waiting"))

    response = []

    for product in query_result:
        response.append(
            {
                'name': product.name,
                'sold': int(product.sold),
                'waiting': int(product.waiting)
            }
        )

    return jsonify(statistics=response), 200


@application.route('/categoryStatistics', methods=["GET"])
@role_check("admin")
def category_statistics():
    query_result = Category.query.outerjoin(ProductCategory).outerjoin \
        (OrderedProducts, ProductCategory.productId == OrderedProducts.productId).group_by(Category.name).order_by \
        (func.sum(func.coalesce(OrderedProducts.requested_quantity, 0)).desc(), Category.name) \
        .with_entities(Category.name).all()

    response = []

    for category in query_result:
        response.append(
            {
                category.name
            }
        )

    return jsonify(statistics=response), 200


if __name__ == '__main__':
    database.init_app(application)
    application.run(debug=True, host='0.0.0.0', port=5003)
