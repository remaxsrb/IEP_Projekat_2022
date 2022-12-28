import csv
import io

from flask import Flask, request, jsonify, json, Response
from flask_jwt_extended import jwt_required
from redis import Redis
from configuration import Configuration
from roleCheck import roleCheck

application = Flask(__name__)
application.config.from_object(Configuration)


@application.route('/update', methods=["POST"])
@jwt_required(refresh=True)
@roleCheck("warehouseworker")
def updateStock():
    if request.files["file"] is None:
        return jsonify(message='Field file missing.'), 400

    content = request.files["file"].stream.read().decode("utf-8")
    stream = io.StringIO(content)
    productReader = csv.reader(stream)

    products = []
    lineNumber = 0

    for productRow in productReader:
        lineNumber += 1

        if len(productRow) != 4:
            return jsonify(message=f'Incorrect number of values on line {lineNumber}.'), 400

        product_amount = productRow[2]
        product_price = productRow[3]

        if int(product_amount) < 1:
            return jsonify(message=f'Incorrect quantity on line {lineNumber}.'), 400
        if float(product_price) < 1.0:
            return jsonify(message=f'Incorrect price on line {lineNumber}.'), 400

        products.append(
            {
                'product_categories': productRow[0],
                'product_name': productRow[1],
                'product_amount': productRow[2],
                'product_price': productRow[3],
            }
        )

    with Redis(host=Configuration.REDIS_HOST, port=6379) as redis:
        for product in products:
            redis.publish(Configuration.REDIS_VOTE_QUEUE, json.dumps(product))
    return Response(status=200)


        # product = Product(name=product_name, price=product_price, stock=product_amount)
        # database.session.add(product)
        # database.session.commit()
        #
        # for category in product_categories_list:
        #     database.session.add(Category(name=category))
        #     database.session.commit()


if __name__ == '__main__':
    application.run(debug=True, host='0.0.0.0', port=80)
