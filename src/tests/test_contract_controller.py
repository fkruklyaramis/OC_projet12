"""
Tests pour les contrôleurs de contrats
Fichier: src/tests/test_contract_controller.py
"""

import pytest
from decimal import Decimal
from unittest.mock import patch
from src.controllers.contract_controller import ContractController
from src.models.contract import ContractStatus
from src.utils.auth_utils import AuthorizationError
from src.utils.validators import ValidationError


class TestContractController:
    """Tests pour le contrôleur des contrats"""

    def test_create_contract_success(self, test_db, test_commercial, test_client):
        """Test de création de contrat réussie"""
        controller = ContractController(test_db)
        controller.current_user = test_commercial

        # Mock des permissions pour autoriser la création
        with patch.object(controller.permission_checker, 'has_permission', return_value=True):
            contract = controller.create_contract(
                client_id=test_client.id,
                total_amount=Decimal("15000.00"),
                amount_due=Decimal("7500.00")
            )

        assert contract is not None
        assert contract.client_id == test_client.id
        assert contract.total_amount == Decimal("15000.00")
        assert contract.amount_due == Decimal("7500.00")
        assert contract.is_signed is False

    def test_create_contract_unauthorized(self, test_db, test_support, test_client):
        """Test de création de contrat sans autorisation"""
        controller = ContractController(test_db)
        controller.current_user = test_support  # Support n'a pas le droit

        with pytest.raises(AuthorizationError):
            controller.create_contract(
                client_id=test_client.id,
                total_amount=Decimal("15000.00"),
                amount_due=Decimal("7500.00")
            )

    def test_create_contract_invalid_client(self, test_db, test_commercial):
        """Test de création de contrat avec client inexistant"""
        controller = ContractController(test_db)
        controller.current_user = test_commercial

        # Mock des permissions pour autoriser la création
        with patch.object(controller.permission_checker, 'has_permission', return_value=True):
            with pytest.raises(ValidationError):
                controller.create_contract(
                    client_id=99999,  # Client inexistant
                    total_amount=Decimal("15000.00"),
                    amount_due=Decimal("7500.00")
                )

    def test_create_contract_invalid_amounts(self, test_db, test_commercial, test_client):
        """Test de création de contrat avec montants invalides"""
        controller = ContractController(test_db)
        controller.current_user = test_commercial

        # Mock des permissions pour autoriser la création
        with patch.object(controller.permission_checker, 'has_permission', return_value=True):
            # Montant dû supérieur au montant total
            with pytest.raises(ValidationError):
                controller.create_contract(
                    client_id=test_client.id,
                    total_amount=Decimal("10000.00"),
                    amount_due=Decimal("15000.00")
                )

    def test_get_all_contracts(self, test_db, test_user, test_contract):
        """Test de récupération de tous les contrats"""
        controller = ContractController(test_db)
        controller.current_user = test_user  # Utilise test_user (gestion) au lieu de test_commercial

        contracts = controller.get_all_contracts()

        assert len(contracts) >= 1
        contract_ids = [contract.id for contract in contracts]
        assert test_contract.id in contract_ids

    def test_get_contract_by_id_success(self, test_db, test_commercial, test_contract):
        """Test de récupération de contrat par ID"""
        controller = ContractController(test_db)
        controller.current_user = test_commercial

        found_contract = controller.get_contract_by_id(test_contract.id)

        assert found_contract is not None
        assert found_contract.id == test_contract.id

    def test_get_contract_by_id_not_found(self, test_db, test_commercial):
        """Test de récupération de contrat inexistant"""
        controller = ContractController(test_db)
        controller.current_user = test_commercial

        found_contract = controller.get_contract_by_id(99999)

        assert found_contract is None

    def test_update_contract_success(self, test_db, test_commercial, test_contract):
        """Test de modification de contrat réussie"""
        controller = ContractController(test_db)
        controller.current_user = test_commercial

        new_amount = Decimal("20000.00")

        updated_contract = controller.update_contract(
            test_contract.id,
            total_amount=new_amount
        )

        assert updated_contract is not None
        assert updated_contract.total_amount == new_amount

    def test_update_contract_unauthorized(self, test_db, test_support, test_contract):
        """Test de modification de contrat sans autorisation"""
        controller = ContractController(test_db)
        controller.current_user = test_support  # Support n'a pas le droit

        with pytest.raises(AuthorizationError):
            controller.update_contract(
                test_contract.id,
                total_amount=Decimal("20000.00")
            )

    def test_sign_contract_success(self, test_db, test_user, test_contract):
        """Test de signature de contrat réussie"""
        controller = ContractController(test_db)
        controller.current_user = test_user  # Gestion peut signer

        with patch('src.services.logging_service.SentryLogger.log_contract_signature'):
            signed_contract = controller.sign_contract(test_contract.id)

        assert signed_contract.status == ContractStatus.SIGNED
        assert signed_contract.signed_date is not None

    def test_sign_contract_unauthorized(self, test_db, test_support, test_contract):
        """Test de signature de contrat sans autorisation"""
        controller = ContractController(test_db)
        controller.current_user = test_support  # Support n'a pas le droit

        with pytest.raises(AuthorizationError):
            controller.sign_contract(test_contract.id)

    def test_sign_contract_already_signed(self, test_db, test_user, test_signed_contract):
        """Test de signature d'un contrat déjà signé"""
        controller = ContractController(test_db)
        controller.current_user = test_user

        with pytest.raises(ValidationError):
            controller.sign_contract(test_signed_contract.id)

    def test_get_unsigned_contracts(self, test_db, test_commercial, test_contract, test_signed_contract):
        """Test de récupération des contrats non signés"""
        controller = ContractController(test_db)
        controller.current_user = test_commercial

        unsigned_contracts = controller.get_unsigned_contracts()

        # Vérifier que le contrat non signé est présent mais pas le signé
        unsigned_ids = [contract.id for contract in unsigned_contracts]
        assert test_contract.id in unsigned_ids
        assert test_signed_contract.id not in unsigned_ids

    def test_get_unpaid_contracts(self, test_db, test_commercial, test_contract):
        """Test de récupération des contrats impayés"""
        controller = ContractController(test_db)
        controller.current_user = test_commercial

        unpaid_contracts = controller.get_unpaid_contracts()

        # Le contrat de test a un montant dû > 0, donc il devrait être dans la liste
        unpaid_ids = [contract.id for contract in unpaid_contracts]
        assert test_contract.id in unpaid_ids

    def test_delete_contract_success(self, test_db, test_user, test_contract):
        """Test de suppression de contrat réussie"""
        controller = ContractController(test_db)
        controller.current_user = test_user  # Gestion peut supprimer

        contract_id = test_contract.id

        result = controller.delete_contract(contract_id)

        assert result is True

        # Vérifier que le contrat a été supprimé
        deleted_contract = controller.get_contract_by_id(contract_id)
        assert deleted_contract is None

    def test_delete_contract_unauthorized(self, test_db, test_commercial, test_contract):
        """Test de suppression de contrat sans autorisation"""
        controller = ContractController(test_db)
        controller.current_user = test_commercial  # Commercial n'a pas le droit

        with pytest.raises(AuthorizationError):
            controller.delete_contract(test_contract.id)
