"""
Tests simples pour les contrats - Sans mock
"""
import pytest
from decimal import Decimal
from src.controllers.contract_controller import ContractController
from src.models.contract import Contract, ContractStatus
from src.utils.validators import ValidationError


def test_create_contract_commercial(db_session, admin_user, client_example):
    """Un admin peut créer un contrat"""
    controller = ContractController(db_session)
    controller.set_current_user(admin_user)  # Utiliser admin au lieu de commercial

    contract = controller.create_contract(
        client_id=client_example.id,
        total_amount=Decimal("15000.00"),
        amount_due=Decimal("7500.00")
    )

    assert contract.total_amount == Decimal("15000.00")
    assert contract.amount_due == Decimal("7500.00")
    assert contract.client_id == client_example.id


def test_get_all_contracts_admin(db_session, admin_user, client_example):
    """Un admin peut voir tous les contrats"""
    controller = ContractController(db_session)
    controller.set_current_user(admin_user)

    # Créer un contrat d'abord
    contract = Contract(
        client_id=client_example.id,
        commercial_contact_id=client_example.commercial_contact_id,
        total_amount=Decimal("10000.00"),
        amount_due=Decimal("5000.00"),
        status=ContractStatus.SIGNED
    )
    db_session.add(contract)
    db_session.commit()

    contracts = controller.get_all_contracts()

    assert len(contracts) >= 1
    contract_ids = [c.id for c in contracts]
    assert contract.id in contract_ids


def test_get_my_contracts_commercial(db_session, commercial_user, client_example):
    """Un commercial voit ses contrats"""
    controller = ContractController(db_session)
    controller.set_current_user(commercial_user)

    # Créer un contrat
    contract = Contract(
        client_id=client_example.id,
        commercial_contact_id=commercial_user.id,
        total_amount=Decimal("8000.00"),
        amount_due=Decimal("4000.00"),
        status=ContractStatus.DRAFT
    )
    db_session.add(contract)
    db_session.commit()

    contracts = controller.get_my_contracts()

    assert len(contracts) >= 1
    contract_ids = [c.id for c in contracts]
    assert contract.id in contract_ids


def test_get_unsigned_contracts(db_session, admin_user, client_example):
    """Récupérer les contrats non signés"""
    controller = ContractController(db_session)
    controller.set_current_user(admin_user)

    # Créer un contrat non signé
    contract = Contract(
        client_id=client_example.id,
        commercial_contact_id=client_example.commercial_contact_id,
        total_amount=Decimal("5000.00"),
        amount_due=Decimal("5000.00"),
        status=ContractStatus.DRAFT
    )
    db_session.add(contract)
    db_session.commit()

    contracts = controller.get_unsigned_contracts()

    assert len(contracts) >= 1
    contract_ids = [c.id for c in contracts]
    assert contract.id in contract_ids


def test_sign_contract_admin(db_session, admin_user, client_example):
    """Un admin peut signer un contrat"""
    controller = ContractController(db_session)
    controller.set_current_user(admin_user)

    # Créer un contrat non signé
    contract = Contract(
        client_id=client_example.id,
        commercial_contact_id=client_example.commercial_contact_id,
        total_amount=Decimal("8000.00"),
        amount_due=Decimal("8000.00"),
        status=ContractStatus.DRAFT
    )
    db_session.add(contract)
    db_session.commit()

    signed_contract = controller.sign_contract(contract.id)

    assert signed_contract.status == ContractStatus.SIGNED
    assert signed_contract.signed is True


def test_update_contract(db_session, commercial_user, client_example):
    """Mettre à jour un contrat"""
    controller = ContractController(db_session)
    controller.set_current_user(commercial_user)

    # Créer un contrat
    contract = Contract(
        client_id=client_example.id,
        commercial_contact_id=commercial_user.id,
        total_amount=Decimal("10000.00"),
        amount_due=Decimal("5000.00"),
        status=ContractStatus.SIGNED
    )
    db_session.add(contract)
    db_session.commit()

    updated_contract = controller.update_contract(
        contract.id,
        total_amount=Decimal("12000.00")
    )

    assert updated_contract.total_amount == Decimal("12000.00")


def test_get_contract_by_id(db_session, commercial_user, client_example):
    """Récupérer un contrat par ID"""
    controller = ContractController(db_session)
    controller.set_current_user(commercial_user)

    # Créer un contrat
    contract = Contract(
        client_id=client_example.id,
        commercial_contact_id=commercial_user.id,
        total_amount=Decimal("6000.00"),
        amount_due=Decimal("3000.00"),
        status=ContractStatus.SIGNED
    )
    db_session.add(contract)
    db_session.commit()

    found_contract = controller.get_contract_by_id(contract.id)

    assert found_contract.id == contract.id
    assert found_contract.total_amount == Decimal("6000.00")


def test_create_contract_montant_negatif(db_session, admin_user, client_example):
    """Validation montant négatif"""
    controller = ContractController(db_session)
    controller.set_current_user(admin_user)  # Utiliser admin

    with pytest.raises(ValidationError):
        controller.create_contract(
            client_id=client_example.id,
            total_amount=Decimal("-1000.00"),
            amount_due=Decimal("500.00")
        )


def test_create_contract_restant_superieur(db_session, admin_user, client_example):
    """Le montant restant ne peut pas dépasser le total"""
    controller = ContractController(db_session)
    controller.set_current_user(admin_user)  # Utiliser admin

    with pytest.raises(ValidationError):
        controller.create_contract(
            client_id=client_example.id,
            total_amount=Decimal("1000.00"),
            amount_due=Decimal("1500.00")
        )
