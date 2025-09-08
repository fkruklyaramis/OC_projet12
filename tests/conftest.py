"""
Configuration globale pour les tests - Tests simples sans mock
"""
import pytest
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.connection import Base
from src.models.user import User, Department
from src.models.client import Client


@pytest.fixture(scope="function")
def db_session():
    """Créer une base de données temporaire pour chaque test"""
    # Fichier temporaire pour la base
    db_fd, db_path = tempfile.mkstemp(suffix='.db')

    # Créer l'engine et les tables
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)

    # Session
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    # Nettoyer
    session.close()
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def admin_user(db_session):
    """Utilisateur admin pour les tests"""
    user = User(
        employee_number="ADMIN001",
        full_name="Admin Test",
        email="admin@test.com",
        department=Department.GESTION
    )
    user.set_password("password123")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def commercial_user(db_session):
    """Utilisateur commercial pour les tests"""
    user = User(
        employee_number="COM001",
        full_name="Commercial Test",
        email="commercial@test.com",
        department=Department.COMMERCIAL
    )
    user.set_password("password123")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def support_user(db_session):
    """Utilisateur support pour les tests"""
    user = User(
        employee_number="SUP001",
        full_name="Support Test",
        email="support@test.com",
        department=Department.SUPPORT
    )
    user.set_password("password123")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def client_example(db_session, commercial_user):
    """Client d'exemple pour les tests"""
    client = Client(
        full_name="Client Test",
        email="client@test.com",
        phone="0123456789",
        company_name="Test Company",
        commercial_contact_id=commercial_user.id
    )
    db_session.add(client)
    db_session.commit()
    return client
