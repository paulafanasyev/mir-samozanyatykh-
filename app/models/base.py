"""
Base models for МИР Самозанятых
Placeholder for SQLAlchemy models migration
"""
from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    name = Column(String)
    role = Column(String, default="user")
    subscription = Column(String, default="start")
    verified = Column(Boolean, default=False)
    phone = Column(String)
    inn = Column(String)
    created_at = Column(DateTime, server_default=func.now())

class Contract(Base):
    __tablename__ = "contracts"
    id = Column(String, primary_key=True)
    user_id = Column(String, index=True)
    title = Column(String)
    type = Column(String)
    client_name = Column(String)
    client_inn = Column(String)
    amount = Column(Float)
    status = Column(String, default="draft")
    created_at = Column(DateTime, server_default=func.now())
    signed = Column(Boolean, default=False)

class FinanceRecord(Base):
    __tablename__ = "finance"
    id = Column(String, primary_key=True)
    user_id = Column(String, index=True)
    type = Column(String)
    amount = Column(Float)
    category = Column(String)
    description = Column(Text)
    date = Column(DateTime, server_default=func.now())
    npd_paid = Column(Boolean, default=False)
