from flask_sqlalchemy import SQLAlchemy

database = SQLAlchemy()


class ProductCategory(database.Model):
    __tablename__ = "productcategories"
    id = database.Column(database.Integer, primary_key=True)
    productId = database.Column(database.Integer, database.ForeignKey("products.id"), nullable=False)
    categoryId = database.Column(database.Integer, database.ForeignKey("categories.id"), nullable=False)


class OrderedProducts(database.Model):
    __tablename__ = "orderedproducts"
    id = database.Column(database.Integer, primary_key=True)
    productId = database.Column(database.Integer, database.ForeignKey("products.id"), nullable=False)
    orderId = database.Column(database.Integer, database.ForeignKey("orders.id"), nullable=False)
    requested_quantity = database.Column(database.Integer, nullable=False)
    received_quantity = database.Column(database.Integer, nullable=False)


class Product(database.Model):
    __tablename__ = "products"
    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(256), nullable=False, unique=True)
    price = database.Column(database.Float, nullable=False)
    stock = database.Column(database.Integer, nullable=False)

    categories = database.relationship("Category", secondary=ProductCategory.__tablename__, back_populates="products")
    orders = database.relationship("Order", secondary=ProductCategory.__tablename__, back_populates="products")


class Category(database.Model):
    __tablename__ = "categories"
    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(256), nullable=False, unique=True)

    products = database.relationship("Product", secondary=ProductCategory.__tablename__, back_populates="categories")


class Order(database.Model):
    __tablename__ = "orders"
    id = database.Column(database.Integer, primary_key=True)
    totalprice = database.Column(database.FLOAT, nullable=False)
    timestamp = database.Column(database.DateTime, nullable=False)
    status = database.Column(database.Boolean, nullable=False)
    customer = database.Column(database.String(256), nullable=False, unique=True)

    products = database.relationship("Product", secondary=ProductCategory.__tablename__, back_populates="orders")
