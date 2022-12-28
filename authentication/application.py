from flask import Flask, request, Response, jsonify
from configuration import Configuration
from models import database, User, UserRole
from email.utils import parseaddr
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, \
    get_jwt_identity
from sqlalchemy import and_

import re

application = Flask(__name__)
application.config.from_object(Configuration)


# noinspection DuplicatedCode
@application.route("/register", methods=["POST"])
def register():
    forename = request.json.get('forename', '')
    surname = request.json.get('surname', '')
    email = request.json.get('email', '')
    password = request.json.get('password', '')
    usertype = request.json.get('isCustomer', 'False')

    if len(forename) == 0:
        return jsonify(message='Field forename is missing.'), 400
    if len(surname) == 0:
        return jsonify(message='Field surname is missing.'), 400
    if len(email) == 0:
        return jsonify(message='Field email is missing.'), 400
    if len(password) == 0:
        return jsonify(message='Field password is missing.'), 400

    result = parseaddr(email)
    if len(result[1]) == 0:
        return jsonify(message='Invalid email.'), 400

    emailExists = User.query.filter(User.email == email).first()

    if emailExists:
        return jsonify(message='Email already exists.'), 400

    passwordValid = re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$", password)

    if not passwordValid:
        return jsonify(message='Invalid password.'), 400

    user = User(email=email, password=password, forename=forename, surname=surname)
    database.session.add(user)
    database.session.commit()

    userRole = None

    if usertype == 'True':
        userRole = UserRole(userId=user.id, roleId=2)
    else:
        userRole = UserRole(userId=user.id, roleId=3)

    database.session.add(userRole)
    database.session.commit()

    return Response("Registration successful!", status=200)


jwt = JWTManager(application)


@application.route('/login', methods=['POST'])
def login():
    email = request.json.get('email', '')
    password = request.json.get('password', '')

    if len(email) == 0:
        return jsonify(message='Field email is missing.'), 400

    if len(password) == 0:
        return jsonify(message='Field password is missing.'), 400

    result = parseaddr(email)
    if len(result[1]) == 0:
        return jsonify(message='Invalid email.'), 400

    user = User.query.filter(and_(User.email == email, User.password == password)).first()

    if not user:
        return jsonify(message='Invalid credentials.'), 400

    additionalClaims = {
        'forename': str(user.forename),
        'surname': str(user.surname),
        'roles': [str(role) for role in user.roles]
    }

    accessToken = create_access_token(identity=user.email, additional_claims=additionalClaims)
    refreshToken = create_refresh_token(identity=user.email, additional_claims=additionalClaims)

    return jsonify(accessToken=accessToken, refreshToken=refreshToken)


@application.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    refreshClaims = get_jwt()

    additionalClaims = {

        'firstname': refreshClaims['firstname'],
        'lastname': refreshClaims['lastname'],
        'roles': refreshClaims['roles']
    }

    return Response(create_access_token(identity=identity, additional_claims=additionalClaims), status=200)


@application.route('/delete', methods=['POST'])
@jwt_required(refresh=True)
def delete():
    email = request.json.get('email', '')

    if len(email) == 0:
        return jsonify(message='Field email is missing.'), 400

    result = parseaddr(email)
    if len(result[1]) == 0:
        return jsonify(message='Invalid email.'), 400

    user = User.query.filter(User.email == email).first()

    if not user:
        return jsonify(message='Unknown user.'), 400

    database.session.delete(user)
    database.session.commit()

    return Response('', status=200)


if __name__ == '__main__':
    database.init_app(application)
    application.run(debug=True, host='0.0.0.0', port=80)
