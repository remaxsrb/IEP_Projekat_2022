from datetime import timedelta
import os

databaseHost = os.environ["MYSQL_HOST"]
databaseUser = os.environ["MYSQL_USER"]
databasePass = os.environ["MYSQL_PASSWORD"]
databaseName = os.environ["MYSQL_DATABASE"]
databasePort = os.environ["MYSQL_PORT"]


class Configuration:
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{databaseUser}:{databasePass}@{databaseHost}:{databasePort}/{databaseName}"
    JWT_SECRET_KEY = "JWTSecretDevKey"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
