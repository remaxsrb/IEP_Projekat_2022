import os

databaseHost = os.environ["MYSQL_HOST"]
databaseUser = os.environ["MYSQL_USER"]
databasePass = os.environ["MYSQL_PASSWORD"]
databaseName = os.environ["MYSQL_DATABASE"]
databasePort = os.environ["MYSQL_PORT"]


class Configuration:
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{databaseUser}:{databasePass}@{databaseHost}:{databasePort}/{databaseName}"
    REDIS_HOST = "redis"
    REDIS_WAREHOUSE_QUEUE = "warehouse_queue"
