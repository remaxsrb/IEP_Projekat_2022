from flask import Flask, request, Response, jsonify
from configuration import Configuration
from models import database, User
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, \
    get_jwt_identity
from sqlalchemy import and_

import re

application = Flask(__name__)
application.config.from_object(Configuration)


@application.route("/register", methods=["POST"])
def register():
    forename = request.json.get('forename', '')
    surname = request.json.get('surname', '')
    email = request.json.get('email', '')
    password = request.json.get('password', '')
    usertype = request.json.get('isCustomer', '')

    # U testovima strinogvi sa jednim blanko znakom se smatraju validnim sto sam ja u kodu stavio kao nevalidno

    if len(forename) == 0 or not forename:
        return jsonify(message='Field forename is missing.'), 400
    if len(surname) == 0 or not surname:
        return jsonify(message='Field surname is missing.'), 400
    if len(email) == 0 or not email:
        return jsonify(message='Field email is missing.'), 400
    if len(password) == 0 or not password:
        return jsonify(message='Field password is missing.'), 400
    if len(str(usertype)) == 0:
        return jsonify(message='Field isCustomer is missing.'), 400

    valid_email = re.fullmatch(r"(^[a-zA-Z0-9]+@[a-zA-Z0-9]+\.[a-z.]{2,}$)", email)

    if not valid_email:
        return jsonify(message='Invalid email.'), 400

    password_valid = 8 <= len(password) <= 256 and re.search(r"\d", password) \
                     and re.search(r"[a-z]", password) and re.search(r"[A-Z]", password)

    if not password_valid:
        return jsonify(message='Invalid password.'), 400

    email_exists = User.query.filter(User.email == email).first()

    if email_exists:
        return jsonify(message='Email already exists.'), 400

    role = "customer" if usertype else "manager"

    user = User(email=email, password=password, forename=forename, surname=surname, role=role)
    database.session.add(user)
    database.session.commit()

    return jsonify(message='Registration successful!'), 200


jwt = JWTManager(application)


@application.route('/login', methods=['POST'])
def login():
    email = request.json.get('email', '')
    password = request.json.get('password', '')

    if len(email) == 0 or not email:
        return jsonify(message='Field email is missing.'), 400

    if len(password) == 0 or not password:
        return jsonify(message='Field password is missing.'), 400

    valid_email = re.fullmatch(r"(^[a-zA-Z0-9]+@[a-zA-Z0-9]+\.[a-z.]{2,}$)", email)

    if not valid_email:
        return jsonify(message='Invalid email.'), 400

    user = User.query.filter(and_(User.email == email, User.password == password)).first()

    if not user:
        return jsonify(message='Invalid credentials.'), 400

    additional_claims = {
        "forename": user.forename,
        "surname": user.surname,
        "roles": user.role
    }

    access_token = create_access_token(identity=user.email, additional_claims=additional_claims)
    refresh_token = create_refresh_token(identity=user.email, additional_claims=additional_claims)

    return jsonify(accessToken=access_token, refreshToken=refresh_token), 200


@application.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    refresh_claims = get_jwt()

    additional_claims = {

        'forename': refresh_claims['forename'],
        'surname': refresh_claims['surname'],
        'roles': refresh_claims['roles']
    }

    access_token = create_access_token(identity=identity, additional_claims=additional_claims)

    return jsonify(accessToken=access_token), 200


@application.route('/delete', methods=['POST'])
@jwt_required(refresh=True)
def delete():
    identity = get_jwt_identity()
    refresh_claims = get_jwt()
    if 'admin' not in refresh_claims['roles']:
        return jsonify(msg='Missing Authorization Header'), 401

    email = request.json.get('email', '')

    if len(email) == 0 or not email:
        return jsonify(message='Field email is missing.'), 400

    valid_email = re.fullmatch(r"(^[a-zA-Z0-9]+@[a-zA-Z0-9]+\.[a-z.]{2,}$)", email)

    if not valid_email:
        return jsonify(message='Invalid email.'), 400

    user = User.query.filter(User.email == email).first()

    if not user:
        return jsonify(message='Unknown user.'), 400

    database.session.delete(user)
    database.session.commit()

    return Response(status=200)


if __name__ == '__main__':
    database.init_app(application)
    application.run(debug=True, host='0.0.0.0', port=5000)
