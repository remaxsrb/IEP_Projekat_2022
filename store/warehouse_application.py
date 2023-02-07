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


# ova metoda je potrebna kako bi se proverilo da li je nesto broj ili ne. Testovi su mi padali jer se nisu samo
# stringovi koji predstavljaju brojeve slali metodama float() i int()
def is_number(string):
    try:
        float(string)
        return True
    except ValueError:
        return False


@application.route('/update', methods=["POST"])
@jwt_required()
@role_check("manager")
def update_stock():
    if "file" not in request.files:
        return Response(json.dumps({"message": "Field file is missing."}), 400)

    content = request.files["file"].stream.read().decode("utf-8")
    stream = io.StringIO(content)
    product_reader = csv.reader(stream)

    products = []
    line_number = 0

    for productRow in product_reader:

        if len(productRow) != 4:
            return Response(json.dumps({"message": f"Incorrect number of values on line {line_number}."}), 400)

        product_amount = productRow[2]
        product_price = productRow[3]

        if not is_number(product_amount) or int(product_amount) <= 0:
            return Response(json.dumps({"message": f"Incorrect quantity on line {line_number}."}), 400)
        if not is_number(product_price) or float(product_price) <= 0.0:
            return Response(json.dumps({"message": f"Incorrect price on line {line_number}."}), 400)

        # zbog nacina na koji redis radi ovde je potrebno parsirati ulazni fajl u suprotnom ce redis baciti izuzetak

        products.append(
            {
                'product_categories': productRow[0],
                'product_name': productRow[1],
                'product_amount': product_amount,
                'product_price': product_price,
            }
        )
        line_number += 1

    with Redis(host=Configuration.REDIS_HOST, port=6379) as redis:
        for product in products:
            redis.rpush(Configuration.REDIS_WAREHOUSE_QUEUE, json.dumps(product))
    return Response(status=200)


if __name__ == '__main__':
    application.run(debug=True, host='0.0.0.0', port=5001)
