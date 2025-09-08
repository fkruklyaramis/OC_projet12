"""
Tests simples pour les événements - Sans mock
"""
import pytest
from datetime import datetime, timedelta, timezone
from src.controllers.event_controller import EventController
from src.models.event import Event
from src.models.contract import Contract, ContractStatus
from src.models.user import User, Department
from src.utils.validators import ValidationError
from decimal import Decimal


def test_create_event_commercial(db_session, commercial_user, client_example):
    """Un commercial peut créer un événement pour son contrat signé"""
    controller = EventController(db_session)
    controller.set_current_user(commercial_user)

    # Créer un contrat signé d'abord
    contract = Contract(
        client_id=client_example.id,
        commercial_contact_id=commercial_user.id,
        total_amount=Decimal("10000.00"),
        amount_due=Decimal("5000.00"),
        status=ContractStatus.SIGNED
    )
    db_session.add(contract)
    db_session.commit()

    start_date = datetime.now(timezone.utc) + timedelta(days=15)
    end_date = start_date + timedelta(hours=6)

    event = controller.create_event(
        name="Nouveau Événement",
        contract_id=contract.id,
        start_date=start_date,
        end_date=end_date,
        location="Lyon",
        attendees=50,
        notes="Notes événement"
    )

    assert event.name == "Nouveau Événement"
    assert event.contract_id == contract.id
    assert event.location == "Lyon"
    assert event.attendees == 50


def test_get_all_events_admin(db_session, admin_user, client_example, support_user):
    """Un admin peut voir tous les événements"""
    controller = EventController(db_session)
    controller.set_current_user(admin_user)

    # Créer un contrat signé et un événement
    contract = Contract(
        client_id=client_example.id,
        commercial_contact_id=client_example.commercial_contact_id,
        total_amount=Decimal("8000.00"),
        amount_due=Decimal("4000.00"),
        status=ContractStatus.SIGNED
    )
    db_session.add(contract)
    db_session.commit()

    start_date = datetime.now(timezone.utc) + timedelta(days=30)
    end_date = start_date + timedelta(hours=8)

    event = Event(
        name="Événement Test",
        contract_id=contract.id,
        start_date=start_date,
        end_date=end_date,
        location="Paris",
        attendees=100,
        support_contact_id=support_user.id
    )
    db_session.add(event)
    db_session.commit()

    events = controller.get_all_events()

    assert len(events) == 1
    assert events[0].id == event.id


def test_get_my_events_support(db_session, support_user, client_example):
    """Un support voit ses événements assignés"""
    controller = EventController(db_session)
    controller.set_current_user(support_user)

    # Créer un contrat et un événement assigné
    contract = Contract(
        client_id=client_example.id,
        commercial_contact_id=client_example.commercial_contact_id,
        total_amount=Decimal("6000.00"),
        amount_due=Decimal("3000.00"),
        status=ContractStatus.SIGNED
    )
    db_session.add(contract)
    db_session.commit()

    start_date = datetime.now(timezone.utc) + timedelta(days=20)
    end_date = start_date + timedelta(hours=4)

    event = Event(
        name="Mon Événement",
        contract_id=contract.id,
        start_date=start_date,
        end_date=end_date,
        location="Marseille",
        attendees=75,
        support_contact_id=support_user.id
    )
    db_session.add(event)
    db_session.commit()

    events = controller.get_my_events()

    assert len(events) == 1
    assert events[0].id == event.id


def test_get_upcoming_events(db_session, admin_user, client_example):
    """Récupérer les événements à venir"""
    controller = EventController(db_session)
    controller.set_current_user(admin_user)

    # Créer un contrat et un événement futur
    contract = Contract(
        client_id=client_example.id,
        commercial_contact_id=client_example.commercial_contact_id,
        total_amount=Decimal("7000.00"),
        amount_due=Decimal("3500.00"),
        status=ContractStatus.SIGNED
    )
    db_session.add(contract)
    db_session.commit()

    start_date = datetime.now(timezone.utc) + timedelta(days=10)
    end_date = start_date + timedelta(hours=3)

    event = Event(
        name="Événement Futur",
        contract_id=contract.id,
        start_date=start_date,
        end_date=end_date,
        location="Nice",
        attendees=60
    )
    db_session.add(event)
    db_session.commit()

    events = controller.get_upcoming_events()

    assert len(events) >= 1
    event_ids = [e.id for e in events]
    assert event.id in event_ids


def test_get_events_without_support(db_session, admin_user, client_example):
    """Récupérer les événements sans support assigné"""
    controller = EventController(db_session)
    controller.set_current_user(admin_user)

    # Créer un contrat et un événement sans support
    contract = Contract(
        client_id=client_example.id,
        commercial_contact_id=client_example.commercial_contact_id,
        total_amount=Decimal("5000.00"),
        amount_due=Decimal("2500.00"),
        status=ContractStatus.SIGNED
    )
    db_session.add(contract)
    db_session.commit()

    start_date = datetime.now(timezone.utc) + timedelta(days=25)
    end_date = start_date + timedelta(hours=5)

    event = Event(
        name="Événement Sans Support",
        contract_id=contract.id,
        start_date=start_date,
        end_date=end_date,
        location="Bordeaux",
        attendees=40,
        support_contact_id=None
    )
    db_session.add(event)
    db_session.commit()

    events = controller.get_events_without_support()

    assert len(events) >= 1
    event_ids = [e.id for e in events]
    assert event.id in event_ids


def test_assign_support_to_event(db_session, admin_user, support_user, client_example):
    """Assigner un support à un événement"""
    controller = EventController(db_session)
    controller.set_current_user(admin_user)

    # Créer un contrat et un événement sans support
    contract = Contract(
        client_id=client_example.id,
        commercial_contact_id=client_example.commercial_contact_id,
        total_amount=Decimal("9000.00"),
        amount_due=Decimal("4500.00"),
        status=ContractStatus.SIGNED
    )
    db_session.add(contract)
    db_session.commit()

    start_date = datetime.now(timezone.utc) + timedelta(days=35)
    end_date = start_date + timedelta(hours=7)

    event = Event(
        name="Événement À Assigner",
        contract_id=contract.id,
        start_date=start_date,
        end_date=end_date,
        location="Toulouse",
        attendees=90
    )
    db_session.add(event)
    db_session.commit()

    updated_event = controller.assign_support_to_event(event.id, support_user.id)

    assert updated_event.support_contact_id == support_user.id


def test_update_event(db_session, support_user, client_example):
    """Modifier un événement"""
    controller = EventController(db_session)
    controller.set_current_user(support_user)

    # Créer un contrat signé avec un commercial
    commercial_user = User(
        full_name="Commercial Test",
        email="commercial-unique@test.com",  # Email unique
        employee_number="789012",  # Numéro unique aussi
        department=Department.COMMERCIAL,
        hashed_password="$argon2id$v=19$m=65536,t=3,p=4$test"  # Hash factice
    )
    db_session.add(commercial_user)
    db_session.commit()

    contract = Contract(
        client_id=client_example.id,
        commercial_contact_id=commercial_user.id,
        total_amount=Decimal("12000.00"),
        amount_due=Decimal("6000.00"),
        status=ContractStatus.SIGNED
    )
    db_session.add(contract)
    db_session.commit()

    start_date = datetime.now(timezone.utc) + timedelta(days=40)
    end_date = start_date + timedelta(hours=6)

    event = Event(
        name="Événement À Modifier",
        contract_id=contract.id,
        support_contact_id=support_user.id,  # Assigner au support qui va modifier
        start_date=start_date,
        end_date=end_date,
        location="Lille",
        attendees=80
    )
    db_session.add(event)
    db_session.commit()

    updated_event = controller.update_event(
        event.id,
        location="Strasbourg",
        attendees=100
    )

    assert updated_event.location == "Strasbourg"
    assert updated_event.attendees == 100


def test_create_event_fin_avant_debut(db_session, commercial_user, client_example):
    """Validation : fin avant début invalide"""
    controller = EventController(db_session)
    controller.set_current_user(commercial_user)

    # Créer un contrat signé
    contract = Contract(
        client_id=client_example.id,
        commercial_contact_id=commercial_user.id,
        total_amount=Decimal("4000.00"),
        amount_due=Decimal("2000.00"),
        status=ContractStatus.SIGNED
    )
    db_session.add(contract)
    db_session.commit()

    start_date = datetime.now(timezone.utc) + timedelta(days=10)
    end_date = start_date - timedelta(hours=2)  # Fin avant début !

    with pytest.raises(ValidationError):
        controller.create_event(
            name="Événement Invalide",
            contract_id=contract.id,
            start_date=start_date,
            end_date=end_date,
            location="Test",
            attendees=10
        )


def test_create_event_participants_negatif(db_session, commercial_user, client_example):
    """Validation : nombre de participants négatif"""
    controller = EventController(db_session)
    controller.set_current_user(commercial_user)

    # Créer un contrat signé
    contract = Contract(
        client_id=client_example.id,
        commercial_contact_id=commercial_user.id,
        total_amount=Decimal("3000.00"),
        amount_due=Decimal("1500.00"),
        status=ContractStatus.SIGNED
    )
    db_session.add(contract)
    db_session.commit()

    start_date = datetime.now(timezone.utc) + timedelta(days=10)
    end_date = start_date + timedelta(hours=2)

    with pytest.raises(ValidationError):
        controller.create_event(
            name="Événement Invalide",
            contract_id=contract.id,
            start_date=start_date,
            end_date=end_date,
            location="Test",
            attendees=-5
        )
