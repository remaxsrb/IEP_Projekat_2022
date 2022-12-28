from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship

from database import Base


class ProductCategory(Base):
    __tablename__ = "productcategories"
    id = Column(Integer, primary_key=True)
    productId = Column(Integer, ForeignKey("products.id"), nullable=False)
    categoryId = Column(Integer, ForeignKey("categories.id"), nullable=False)


class OrderedProducts(Base):
    __tablename__ = "orderedproducts"
    id = Column(Integer, primary_key=True)
    productId = Column(Integer, ForeignKey("products.id"), nullable=False)
    orderId = Column(Integer, ForeignKey("orders.id"), nullable=False)
    requested_quantity = Column(Integer, nullable=False)
    received_quantity = Column(Integer, nullable=False)


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False, unique=True)
    price = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False)

    # categories = relationship("Category", secondary=ProductCategory.__tablename__, back_populates="products")
    # orders = relationship("Order", secondary=ProductCategory.__tablename__, back_populates="products")


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False, unique=True)

    # products = relationship("Product", secondary=ProductCategory.__tablename__, back_populates="categories")


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    totalprice = Column(Float, nullable=False)
    timeofcreation = Column(DateTime, nullable=False)
    status = Column(Boolean, nullable=False)

    # products = relationship("Product", secondary=ProductCategory.__tablename__, back_populates="orders")
