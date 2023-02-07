from flask import Flask, request, json, Response
from flask_jwt_extended import jwt_required, get_jwt_identity, JWTManager, get_jwt
from configuration import Configuration
from roleCheck import role_check
from models import Product, ProductCategory, Category, Order, database, OrderedProduct
from sqlalchemy import and_, or_
from datetime import datetime

application = Flask(__name__)
application.config.from_object(Configuration)
jwt = JWTManager(application)


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


@application.route('/search', methods=["GET"])
@jwt_required()
@role_check("customer")
def search():
    name = request.args.get("name")
    category = request.args.get("category")

    categories = Category.query.all()
    products = Product.query.all()

    if name is not None:
        products = Product.query.filter(Product.name.like(f"%{name}%")).all()

        categories = Category.query.join(ProductCategory).join(Product).filter(
            Product.name.like(f"%{name}%")).all()

    if category is not None:
        categories = Category.query.filter(Category.name.like(f"%{category}%")).all()

        products = Product.query.join(ProductCategory).join(Category).filter(
            Category.name.like(f"%{category}%")).all()

    categories = [category.name for category in categories]

    products = [{
        "categories": [category.name for category in product.categories],
        "id": product.id,
        "name": product.name,
        "price": product.price,
        "quantity": product.stock
    } for product in products]

    response = {
        "categories": categories,
        "products": products
    }

    return Response(json.dumps(response), status=200)


@application.route('/order', methods=["POST"])
@jwt_required()
@role_check("customer")
def order():
    if "requests" not in request.json:
        return Response(json.dumps({"message": "Field requests is missing."}), status=400)

    customer = get_jwt_identity()

    requests = request.json.get("requests")
    request_number = 0
    total_price = 0.0

    for req in requests:

        if "id" not in req:
            return Response(json.dumps({"message": f"Product id is missing for request number {request_number}."}),
                            status=400)
        if "quantity" not in req:
            return Response(
                json.dumps({"message": f"Product quantity is missing for request number {request_number}."}),
                status=400)

        requested_product_id = req["id"]
        requested_product_quantity = req["quantity"]

        if not is_number(requested_product_id) or int(requested_product_id) < 1:
            return Response(json.dumps({"message": f"Invalid product id for request number {request_number}."}),
                            status=400)
        if not is_number(requested_product_quantity) or int(requested_product_quantity) < 1:
            return Response(json.dumps({"message": f"Invalid product quantity for request number {request_number}."}),
                            status=400)
        if Product.query.filter(Product.id == requested_product_id).first() is None:
            return Response(json.dumps({"message": f"Invalid product for request number {request_number}."}),
                            status=400)

        total_product_price = Product.query.filter(
            Product.id == requested_product_id).first().price * requested_product_quantity

        total_price += total_product_price
        request_number += 1

    new_order = Order(price=total_price, status="PENDING", customer=customer)
    database.session.add(new_order)
    database.session.commit()

    waiting = True

    # mozda postoji bolje resenje od toga da dva puta prolazim kroz request niz

    for req in requests:
        requested_product_id = req["id"]
        requested_product_quantity = req["quantity"]

        product = Product.query.filter(Product.id == requested_product_id).first()

        if product.stock >= requested_product_quantity:
            ordered_product = OrderedProduct(order_id=new_order.id, product_id=product.id,
                                             received_quantity=requested_product_quantity,
                                             requested_quantity=requested_product_quantity, price=product.price)
            database.session.add(ordered_product)
            product.stock -= requested_product_quantity
            database.session.commit()
            waiting = False
        else:
            ordered_product = OrderedProduct(order_id=new_order.id, product_id=product.id, received_quantity=product.stock,
                                             requested_quantity=requested_product_quantity, price=product.price)
            database.session.add(ordered_product)
            product.stock = 0
            database.session.commit()

    if not waiting:
        new_order.status = "COMPLETE"
        database.session.commit()

    return Response(json.dumps({"id": new_order.id}), 200)


@application.route('/status', methods=["GET"])
@role_check("customer")
def status():
    customer = get_jwt_identity()
    orders = Order.query.filter(Order.customer == customer).all()

    orders = [{
        "products": [{
            "categories": [category.name for category in product.categories],
            "name": product.name,
            "price": OrderedProduct.query.filter(OrderedProduct.order_id == current_order.id,
                                                 OrderedProduct.product_id == product.id).first().price,
            "received": OrderedProduct.query.filter(OrderedProduct.order_id == current_order.id,
                                                    OrderedProduct.product_id == product.id).first().received_quantity,
            "requested": OrderedProduct.query.filter(OrderedProduct.order_id == current_order.id,
                                                     OrderedProduct.product_id == product.id).first().requested_quantity,
        } for product in current_order.products],
        "price": current_order.price,
        "status": current_order.status,
        "timestamp": current_order.timestamp
    } for current_order in orders]

    return Response(json.dumps({"orders": orders}), 200)


if __name__ == '__main__':
    database.init_app(application)
    application.run(debug=True, host='0.0.0.0', port=5002)
