from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from flask import Response, jsonify


def role_check(role):
    def inner_role(function):
        @wraps(function)
        def decorator(*arguments, **keyword_arguments):
            verify_jwt_in_request()
            claims = get_jwt()
            if ("roles" in claims) and (role in claims["roles"]):
                return function(*arguments, **keyword_arguments)
            else:
                return jsonify(msg='Missing Authorization Header'), 401

        return decorator

    return inner_role
