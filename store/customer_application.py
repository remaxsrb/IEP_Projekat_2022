from flask import Flask, request, jsonify, json, Response
from flask_jwt_extended import jwt_required, get_jwt_identity, JWTManager, get_jwt
from configuration import Configuration
from roleCheck import role_check
from models import Product, ProductCategory, Category, Order, database, OrderedProducts
from sqlalchemy import and_, or_
from datetime import datetime

application = Flask(__name__)
application.config.from_object(Configuration)
jwt = JWTManager(application)


@application.route('/search?name=<PRODUCT_NAME>&category=<CATEGORY_NAME>', methods=["GET"])
# @role_check("customer")
def search(name, category):
    refresh_claims = get_jwt()
    if refresh_claims["roles"].strip() not in ["customer"]:
        return jsonify(msg="Missing authorization header"), 401

    # kategorije koje sadrze category parametar u nazivu
    categories = Category.query.join(ProductCategory).join(Product).filter(
        and_(
            *[Category.name.like(f"%{category}%")],
            *[Product.name.like(f"%{name}%")]
        )
    ).all()

    # proizvodi koje sadrze product parametar u nazivu
    products = Product.query.join(ProductCategory).join(Category).filter(
        and_(
            *[Product.name.like(f"%{name}%")],
            *[Category.name.like(f"%{category}%")]

        )
    ).all()

    response = {
        "categories": jsonify(categories),
        "products": jsonify(products)
    }

    return response, 400


@application.route('/order', methods=["POST"])
# @role_check("customer")
def order():
    refresh_claims = get_jwt()
    if refresh_claims["roles"].strip() not in ["customer"]:
        return jsonify(msg="Missing authorization header"), 401

    requests = [item.strip() for item in request.json.get('requests', '').split(",")]
    customer = get_jwt_identity()
    if len(requests) == 0:
        return jsonify(message='Field requests is missing.'), 400

    existing_products = Product.query.all()

    existing_ids = []
    for product in existing_products:
        existing_ids.append(product.id)

    request_number = 0
    total_price = 0.0
    order_status = True
    requested_product = None
    ordered_products = []
    for req in requests:

        requested_product_id = req.json.get('id', '')
        requested_product_quantity = req.json.get('quantity', '')

        if len(requested_product_id) == 0:
            return jsonify(message=f'Field id is missing for request number {request_number}.'), 400
        if len(requested_product_quantity) == 0:
            return jsonify(message=f'Field quantity is missing for request number {request_number}.'), 400

        if int(requested_product_id) < 1:
            return jsonify(message=f'Invalid product id for request number{request_number}.'), 400
        if int(requested_product_quantity) < 1:
            return jsonify(message=f'Invalid product quantity for request number {request_number}.'), 400

        if int(requested_product_id) not in existing_ids:
            return jsonify(message=f'Invalid product for request number {request_number}.'), 400

        for product in existing_products:
            if product.id != int(requested_product_id):
                pass
            requested_quantity = 0

            if product.stock < int(requested_product_quantity):
                order_status = False
                requested_quantity = product.stock
            else:
                requested_quantity = requested_product_quantity

            requested_product_meta = {
                "requested_product_id": requested_product_id,
                "requested_product_quantity": requested_product_quantity,
                "requested_quantity": requested_quantity
            }

            ordered_products.append(requested_product_meta)
            total_price += product.stock * product.price
            break

        request_number += 1

    order = Order(totalprice=total_price, timestamp=datetime.fromisoformat(str(datetime.now())),
                  status=order_status, customer=customer)
    database.session.add(order)
    database.session.commit()

    for product in ordered_products:
        ordered_product = OrderedProducts(
            productId=product.get("requested_product_id"),
            orderId=order.id,
            requested_quantity=product.get("requested_product_quantity"),
            received_quantity="requested_quantity")
        database.session.add(ordered_product)
        database.session.commit()

    return jsonify(message=f'id:{order.id}'), 200


@application.route('/status', methods=["GET"])
@role_check("customer")
def status():

    customer = get_jwt_identity()
    orders = Order.query.filter(Order.customer == customer).all()

    response = []
    for current_order in orders:

        ordered_products = Product.query.join(OrderedProducts).join(Order).filter(
            and_(
                *[Order.id == current_order.id],

            )
        ).all()

        response_products = []

        for product in ordered_products:
            categories = Product.query.join(ProductCategory).join(Category).filter(
                and_(
                    *[Product.id == product.id],

                )
            ).all()

            category_names = database.session.query(Category.name).join(ProductCategory).join(Product).filter(
                Product.id == product.id
            )
            response_product = {
                "categories": category_names,
                "name": product.name,
                "received": OrderedProducts.query.filter_by(productId=product.id).first().received_quantity,
                "requested": OrderedProducts.query.filter_by(productId=product.id).first().requested_quantity
            }
            response_products.append(response_product)

        ord = {
            "products": response_products,
            "price": float(current_order.totalprice),
            "status": current_order.orderstatus,
            "timestamp": str(current_order.timestamp)
        }

        response.append(ord)

    return jsonify(orders=response), 200


if __name__ == '__main__':
    application.run(debug=True, host='0.0.0.0', port=5002)
