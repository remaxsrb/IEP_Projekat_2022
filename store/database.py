from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from configuration import Configuration
from sqlalchemy.orm import sessionmaker

engine = create_engine(Configuration.SQLALCHEMY_DATABASE_URI)

Base = declarative_base()

Session = sessionmaker(bind = engine)
