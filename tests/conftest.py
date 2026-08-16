"""Pytest configuration and fixtures"""
import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base, get_db
from app.core.security import get_password_hash

# Test database
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def db_engine():
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def test_user_data():
    return {
        "email": "test@example.com",
        "password": "SecurePass123!",
        "full_name": "Тестовый Пользователь",
        "phone": "+79123456789",
        "inn": "123456789012"
    }

@pytest.fixture
def test_contract_data():
    return {
        "title": "Тестовый договор",
        "client_name": "ООО Ромашка",
        "client_email": "client@example.com",
        "amount": 50000.0,
        "description": "Разработка сайта",
        "contract_type": "gpd"
    }
