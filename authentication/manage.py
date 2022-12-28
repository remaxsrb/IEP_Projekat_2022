from flask import Flask
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from configuration import Configuration
from models import database
from sqlalchemy_utils import database_exists, create_database

application = Flask(__name__)
application.config.from_object(Configuration)

database.init_app(application)

migrate = Migrate(application, database)

manager = Manager(application)
manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    if not database_exists(Configuration.SQLALCHEMY_DATABASE_URI):
        create_database(Configuration.SQLALCHEMY_DATABASE_URI)
    manager.run()
