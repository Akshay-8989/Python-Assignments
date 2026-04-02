from sqlalchemy import Column, Integer, String, Float, DateTime
from db import Base

class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(Integer, primary_key=True, index=True)
    country = Column(String)


class Product(Base):
    __tablename__ = "products"

    stock_code = Column(String, primary_key=True, index=True)
    description = Column(String)
    unit_price = Column(Float)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    invoice_no = Column(String)
    customer_id = Column(Integer, index=True)
    stock_code = Column(String, index=True)
    description = Column(String)
    quantity = Column(Integer)
    unit_price = Column(Float)
    invoice_date = Column(DateTime)
    country = Column(String)