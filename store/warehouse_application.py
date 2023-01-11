import csv
import io

from flask import Flask, request, jsonify, json, Response
from flask_jwt_extended import jwt_required, JWTManager
from redis import Redis
from configuration import Configuration
from roleCheck import role_check

application = Flask(__name__)
application.config.from_object(Configuration)
jwt = JWTManager(application)


@application.route('/update', methods=["POST"])
@jwt_required()
@role_check("manager")
def update_stock():

    if request.files["file"] is None:
        return jsonify(message='Field file missing.'), 400

    content = request.files["file"].stream.read().decode("utf-8")
    stream = io.StringIO(content)
    product_reader = csv.reader(stream)

    products = []
    line_number = 0

    for productRow in product_reader:
        line_number += 1

        if len(productRow) != 4:
            return jsonify(message=f'Incorrect number of values on line {line_number}.'), 400

        product_amount = productRow[2]
        product_price = productRow[3]

        if int(product_amount) < 1:
            return jsonify(message=f'Incorrect quantity on line {line_number}.'), 400
        if float(product_price) < 1.0:
            return jsonify(message=f'Incorrect price on line {line_number}.'), 400

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
            redis.publish(Configuration.REDIS_WAREHOUSE_QUEUE, json.dumps(product))
    return Response(status=200)


if __name__ == '__main__':
    application.run(debug=True, host='0.0.0.0', port=5001)
