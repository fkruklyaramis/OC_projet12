"""
Tests pour les services - focus sur la couverture
Fichier: src/tests/test_services_coverage.py
"""

import pytest
from unittest.mock import Mock, patch
from src.services.logging_service import SentryLogger
from src.utils.hash_utils import hash_password, verify_password
from src.utils.validators import ValidationError, DataValidator


class TestServicesCoverage:
    """Tests pour améliorer la couverture des services"""

    def test_hash_password_success(self):
        """Test de hashage de mot de passe"""
        password = "test_password"
        hashed = hash_password(password)

        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_success(self):
        """Test de vérification de mot de passe"""
        password = "test_password"
        hashed = hash_password(password)

        assert verify_password(hashed, password) is True

    def test_verify_password_failure(self):
        """Test de vérification de mot de passe incorrect"""
        password = "test_password"
        wrong_password = "wrong_password"
        hashed = hash_password(password)

        assert verify_password(hashed, wrong_password) is False

    def test_data_validator_valid_emails(self):
        """Test de validation d'emails valides"""
        validator = DataValidator()

        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org"
        ]

        for email in valid_emails:
            result = validator.validate_email(email)
            assert result == email

    def test_data_validator_invalid_emails(self):
        """Test de validation d'emails invalides"""
        validator = DataValidator()

        invalid_emails = [
            "invalid",
            "@domain.com",
            "user@",
            "user@domain",
            "",
            None
        ]

        for email in invalid_emails:
            with pytest.raises(ValidationError):
                validator.validate_email(email)

    @patch('src.services.logging_service.sentry_sdk')
    def test_sentry_logger_initialization(self, mock_sentry):
        """Test d'initialisation du logger Sentry"""
        logger = SentryLogger()
        assert logger is not None

    @patch('src.services.logging_service.sentry_sdk')
    def test_sentry_logger_log_event(self, mock_sentry):
        """Test de log d'événement - test de la méthode log_exception"""
        logger = SentryLogger()

        # Test avec log_exception qui existe vraiment
        test_exception = Exception("Test exception")
        logger.log_exception(test_exception, {"context": "test"})
        # Le test passe si aucune exception n'est levée

    @patch('src.services.logging_service.sentry_sdk')
    def test_sentry_logger_log_user_creation(self, mock_sentry):
        """Test de log de création d'utilisateur"""
        logger = SentryLogger()

        # Mock user
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.full_name = "Test User"
        mock_user.department.value = "commercial"

        mock_creator = Mock()
        mock_creator.full_name = "Admin User"

        logger.log_user_creation(mock_user, mock_creator)
        # Le test passe si aucune exception n'est levée

    @patch('src.services.logging_service.sentry_sdk')
    def test_sentry_logger_log_contract_signature(self, mock_sentry):
        """Test de log de signature de contrat"""
        logger = SentryLogger()

        # Mock contract avec des types numériques appropriés
        mock_contract = Mock()
        mock_contract.id = 1
        mock_contract.total_amount = 1000.0  # déjà float
        mock_contract.amount_due = 500.0     # déjà float
        mock_contract.client.company_name = "Test Company"

        mock_user = Mock()
        mock_user.id = 1
        mock_user.full_name = "Test User"
        mock_user.email = "test@example.com"
        mock_user.department.value = "GESTION"

        logger.log_contract_signature(mock_contract, mock_user)
        # Le test passe si aucune exception n'est levée

    def test_password_validation_strength(self):
        """Test de validation de force de mot de passe"""
        # Ce test couvre les utilitaires de validation
        strong_passwords = [
            "StrongP@ssw0rd123",
            "C0mpl3x!P@ssw0rd",
            "V3ry$tr0ng!P@ss"
        ]

        for password in strong_passwords:
            # Test que le mot de passe peut être hashé sans erreur
            hashed = hash_password(password)
            assert hashed is not None
            assert verify_password(hashed, password) is True
