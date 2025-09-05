"""
Configuration et fixtures communes pour les tests
Fichier: src/tests/conftest.py
"""

import pytest
import os
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.connection import Base
from src.models.user import User, Department
from src.models.client import Client
from src.models.contract import Contract, ContractStatus
from src.models.event import Event
from decimal import Decimal
from datetime import datetime, timedelta


@pytest.fixture(scope="function")
def test_db():
    """Créer une base de données de test temporaire pour chaque test"""
    # Créer un fichier temporaire pour la base de données
    db_fd, db_path = tempfile.mkstemp(suffix='.db')

    try:
        # Configurer la base de données de test
        test_engine = create_engine(f'sqlite:///{db_path}', echo=False)
        TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

        # Créer les tables
        Base.metadata.create_all(bind=test_engine)

        # Créer une session
        session = TestSessionLocal()

        yield session

        # Nettoyer après le test
        session.close()

    finally:
        # Supprimer le fichier temporaire
        os.close(db_fd)
        os.unlink(db_path)


@pytest.fixture(scope="function")
def test_user(test_db):
    """Créer un utilisateur de test"""
    user = User(
        email="test@epicevents.com",
        full_name="Test User",
        employee_number="EE000001",
        department=Department.GESTION
    )
    user.set_password("TestPassword123!")

    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    return user


@pytest.fixture(scope="function")
def test_commercial(test_db):
    """Créer un utilisateur commercial de test"""
    user = User(
        email="commercial@epicevents.com",
        full_name="Commercial User",
        employee_number="EE000002",
        department=Department.COMMERCIAL
    )
    user.set_password("TestPassword123!")

    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    return user


@pytest.fixture(scope="function")
def test_support(test_db):
    """Créer un utilisateur support de test"""
    user = User(
        email="support@epicevents.com",
        full_name="Support User",
        employee_number="EE000003",
        department=Department.SUPPORT
    )
    user.set_password("TestPassword123!")

    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    return user


@pytest.fixture(scope="function")
def test_client(test_db, test_commercial):
    """Créer un client de test"""
    client = Client(
        company_name="Test Company",
        full_name="John Doe",
        email="john@testcompany.com",
        phone="0123456789",
        commercial_contact_id=test_commercial.id
    )

    test_db.add(client)
    test_db.commit()
    test_db.refresh(client)

    return client


@pytest.fixture(scope="function")
def test_contract(test_db, test_client, test_commercial):
    """Créer un contrat de test"""
    contract = Contract(
        client_id=test_client.id,
        commercial_contact_id=test_commercial.id,
        total_amount=Decimal("10000.00"),
        amount_due=Decimal("5000.00"),
        signed=False,
        status=ContractStatus.DRAFT
    )

    test_db.add(contract)
    test_db.commit()
    test_db.refresh(contract)

    return contract


@pytest.fixture(scope="function")
def test_signed_contract(test_db, test_client, test_commercial):
    """Créer un contrat signé de test"""
    from datetime import datetime
    contract = Contract(
        client_id=test_client.id,
        commercial_contact_id=test_commercial.id,
        total_amount=Decimal("15000.00"),
        amount_due=Decimal("0.00"),
        signed=True,
        status=ContractStatus.SIGNED,
        signed_at=datetime.now()
    )

    test_db.add(contract)
    test_db.commit()
    test_db.refresh(contract)

    return contract


@pytest.fixture(scope="function")
def test_event(test_db, test_signed_contract, test_support):
    """Créer un événement de test"""
    event = Event(
        contract_id=test_signed_contract.id,
        name="Test Event",
        start_date=datetime.now() + timedelta(days=30),
        end_date=datetime.now() + timedelta(days=32),
        location="Test Location",
        attendees=100,
        notes="Test event notes",
        support_contact_id=test_support.id
    )

    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)

    return event


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Configurer des variables d'environnement pour les tests"""
    monkeypatch.setenv("JWT_SECRET_KEY", "test_secret_key_for_testing_only")
    monkeypatch.setenv("SENTRY_DSN", "")  # Désactiver Sentry pendant les tests
    monkeypatch.setenv("SENTRY_ENVIRONMENT", "test")
