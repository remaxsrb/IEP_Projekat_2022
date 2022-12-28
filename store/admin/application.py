from flask import Flask, request, Response, jsonify
from configuration import Configuration
from models import database, Product, Category, ProductCategory, OrderedProducts, Order
from roleCheck import roleCheck
from email.utils import parseaddr
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, \
    get_jwt_identity
from sqlalchemy import and_, func

application = Flask(__name__)
application.config.from_object(Configuration)


@application.route('/productStatistics', methods=["GET"])
@roleCheck("admin")
def productStatistics():
    query_result = database.session.query(
        Product.name,
        func.sum(OrderedProducts.requested_quantity),
        func.sum(OrderedProducts.received_quantity)) \
        .join(OrderedProducts).join(Order).all()

    response = []

    for row in query_result:

        pass


@application.route('/categoryStatistics', methods=["GET"])
@roleCheck("admin")
def categoryStatistics():
    pass


if __name__ == '__main__':
    database.init_app(application)
    application.run(debug=True, host='0.0.0.0', port=80)
