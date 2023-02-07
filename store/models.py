from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime, func

database = SQLAlchemy()


class ProductCategory(database.Model):
    __tablename__ = "product_category"

    id = database.Column(database.Integer, primary_key=True)
    product_id = database.Column(database.Integer, database.ForeignKey("products.id"), nullable=False)
    category_id = database.Column(database.Integer, database.ForeignKey("categories.id"), nullable=False)


class OrderedProduct(database.Model):
    __tablename__ = "ordered_product"

    id = database.Column(database.Integer, primary_key=True)
    order_id = database.Column(database.Integer, database.ForeignKey("orders.id"), nullable=False)
    product_id = database.Column(database.Integer, database.ForeignKey("products.id"), nullable=False)
    price = database.Column(database.Float, nullable=False)
    received_quantity = database.Column(database.Integer, nullable=False)
    requested_quantity = database.Column(database.Integer, nullable=False)


class Product(database.Model):
    __tablename__ = "products"

    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(256), nullable=False)
    price = database.Column(database.Float, nullable=False)
    stock = database.Column(database.Integer, nullable=False)

    categories = database.relationship("Category", secondary=ProductCategory.__table__, back_populates="products")
    orders = database.relationship("Order", secondary=OrderedProduct.__table__, back_populates="products")


class Category(database.Model):
    __tablename__ = "categories"

    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(256), nullable=False)

    products = database.relationship("Product", secondary=ProductCategory.__table__, back_populates="categories")


class Order(database.Model):
    __tablename__ = "orders"

    id = database.Column(database.Integer, primary_key=True)
    price = database.Column(database.Float, nullable=False)
    status = database.Column(database.String(256), nullable=False)
    timestamp = database.Column(DateTime(timezone=False), server_default=func.now())
    customer = database.Column(database.String(256), nullable=False)

    products = database.relationship("Product", secondary=OrderedProduct.__table__, back_populates="orders")