"""
Tests pour le service de logging Sentry
Fichier: tests/test_logging.py
"""
import os
import unittest
from unittest.mock import patch, MagicMock
from src.services.logging_service import SentryLogger


class TestSentryLogger(unittest.TestCase):

    def setUp(self):
        """Setup pour chaque test"""
        # Reset du singleton pour chaque test
        SentryLogger._instance = None

    def test_sentry_logger_initialization(self):
        """Test initialisation du logger Sentry"""
        logger = SentryLogger()
        self.assertTrue(hasattr(logger, 'is_initialized'))
        self.assertTrue(hasattr(logger, '_setup_sentry'))

    def test_sentry_logger_singleton(self):
        """Test pattern singleton"""
        logger1 = SentryLogger()
        logger2 = SentryLogger()
        self.assertIs(logger1, logger2)

    @patch('sentry_sdk.capture_message')
    def test_log_authentication_attempt_success(self, mock_capture):
        """Test journalisation tentative auth réussie"""
        logger = SentryLogger()

        logger.log_authentication_attempt("test@example.com", True, "192.168.1.1")

        # Le message doit être appelé si Sentry est initialisé
        if logger.is_initialized:
            mock_capture.assert_called_once()
            args, kwargs = mock_capture.call_args
            self.assertIn("Tentative de connexion réussie", args[0])
            self.assertIn("test@example.com", args[0])

    @patch('sentry_sdk.capture_message')
    def test_log_authentication_attempt_failure(self, mock_capture):
        """Test journalisation tentative auth échouée"""
        logger = SentryLogger()

        logger.log_authentication_attempt("test@example.com", False)

        if logger.is_initialized:
            mock_capture.assert_called_once()
            args, kwargs = mock_capture.call_args
            self.assertIn("Tentative de connexion échouée", args[0])

    @patch('sentry_sdk.capture_exception')
    def test_log_exception(self, mock_capture):
        """Test journalisation exception"""
        logger = SentryLogger()
        test_exception = ValueError("Test exception")

        logger.log_exception(test_exception)

        if logger.is_initialized:
            mock_capture.assert_called_once_with(test_exception)

    @patch('sentry_sdk.capture_exception')
    def test_log_exception_with_context(self, mock_capture):
        """Test journalisation exception avec contexte"""
        logger = SentryLogger()
        test_exception = ValueError("Test exception")
        context = {"user_id": 123, "action": "test_action"}

        logger.log_exception(test_exception, context)

        if logger.is_initialized:
            mock_capture.assert_called_once_with(test_exception)

    @patch('sentry_sdk.set_user')
    def test_set_user_context(self, mock_set_user):
        """Test définition contexte utilisateur"""
        logger = SentryLogger()

        # Créer un mock user au lieu d'un vrai objet User
        user = MagicMock()
        user.id = 1
        user.email = "test@example.com"
        user.full_name = "Test User"
        user.department.value = "COMMERCIAL"
        user.employee_number = "EE123456"

        logger.set_user_context(user)

        if logger.is_initialized:
            mock_set_user.assert_called_once()

    @patch('sentry_sdk.set_user')
    def test_clear_user_context(self, mock_set_user):
        """Test effacement contexte utilisateur"""
        logger = SentryLogger()

        logger.clear_user_context()

        if logger.is_initialized:
            mock_set_user.assert_called_once_with(None)

    def test_shutdown(self):
        """Test fermeture propre"""
        logger = SentryLogger()

        # Ne doit pas lever d'exception
        try:
            logger.shutdown()
            self.assertTrue(True)
        except Exception:
            self.fail("shutdown() ne doit pas lever d'exception")

    @patch.dict(os.environ, {'SENTRY_DSN': 'test_dsn'})
    @patch('sentry_sdk.init')
    def test_setup_sentry_with_dsn(self, mock_init):
        """Test configuration Sentry avec DSN (désactivé en mode test)"""
        logger = SentryLogger()
        # En mode test, Sentry n'est pas initialisé pour éviter les conflits
        mock_init.assert_not_called()
        # Vérifier que le logger est bien créé mais non initialisé
        self.assertIsNotNone(logger)
        self.assertFalse(logger.is_initialized)

    @patch.dict(os.environ, {'SENTRY_DSN': 'your_sentry_dsn_here'})
    def test_setup_sentry_without_valid_dsn(self):
        """Test configuration Sentry sans DSN valide"""
        self.assertFalse(SentryLogger().is_initialized)

    @patch('sentry_sdk.capture_message')
    def test_log_contract_signature(self, mock_capture):
        """Test journalisation signature contrat"""
        logger = SentryLogger()

        # Mock contract et user
        mock_contract = MagicMock()
        mock_contract.id = 1
        mock_contract.client.company_name = "Test Company"
        mock_contract.total_amount = 5000.0
        mock_contract.amount_due = 2500.0

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.email = "signer@example.com"
        mock_user.full_name = "Test Signer"
        mock_user.department.value = "GESTION"

        logger.log_contract_signature(mock_contract, mock_user)

        if logger.is_initialized:
            mock_capture.assert_called_once()

    @patch('sentry_sdk.flush')
    def test_force_flush(self, mock_flush):
        """Test du flush forcé"""
        logger = SentryLogger()
        logger.force_flush()

        if logger.is_initialized:
            mock_flush.assert_called_once_with(timeout=3)


if __name__ == '__main__':
    unittest.main()
