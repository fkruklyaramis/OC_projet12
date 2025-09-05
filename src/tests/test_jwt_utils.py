"""
Tests pour la génération et validation des tokens JWT
Fichier: src/tests/test_jwt_utils.py
"""

import pytest
from unittest.mock import patch, mock_open
from src.utils.jwt_utils import JWTManager


class TestJWTManager:
    """Tests pour le gestionnaire JWT"""

    @pytest.fixture
    def jwt_manager(self, mock_env_vars):
        """Créer une instance de JWTManager pour les tests"""
        return JWTManager()

    def test_generate_token_success(self, jwt_manager):
        """Test de génération de token JWT réussie"""
        token = jwt_manager.generate_token(
            user_id=1,
            email="test@example.com",
            department="commercial",
            employee_number="EE123456"
        )

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50  # Un JWT fait normalement plus de 50 caractères

    def test_verify_token_success(self, jwt_manager):
        """Test de vérification de token valide"""
        token = jwt_manager.generate_token(
            user_id=123,
            email="test@example.com",
            department="commercial",
            employee_number="EE123456"
        )

        payload = jwt_manager.verify_token(token)

        assert payload is not None
        assert payload.get('user_id') == 123
        assert payload.get('email') == "test@example.com"
        assert 'exp' in payload
        assert 'iat' in payload

    def test_verify_token_invalid(self, jwt_manager):
        """Test de vérification de token invalide"""
        invalid_token = "invalid.token.here"

        payload = jwt_manager.verify_token(invalid_token)

        assert payload is None

    def test_verify_token_malformed(self, jwt_manager):
        """Test de vérification de token malformé"""
        malformed_token = "not.a.jwt"

        payload = jwt_manager.verify_token(malformed_token)

        assert payload is None

    @patch('builtins.open', new_callable=mock_open)
    @patch('src.utils.jwt_utils.Path.mkdir')
    @patch('os.chmod')
    def test_save_token_success(self, mock_chmod, mock_mkdir, mock_file, jwt_manager):
        """Test de sauvegarde de token réussie"""
        token = "test.jwt.token"

        result = jwt_manager.save_token(token)

        assert result is True
        mock_file.assert_called_once_with(jwt_manager.token_file, 'w')

    @patch('builtins.open',
           new_callable=mock_open,
           read_data='{"token": "test.jwt.token", "created_at": "2023-01-01T00:00:00"}')
    @patch('src.utils.jwt_utils.Path.exists')
    def test_load_token_success(self, mock_exists, mock_file, jwt_manager):
        """Test de chargement de token réussi"""
        mock_exists.return_value = True

        token = jwt_manager.load_token()

        assert token == "test.jwt.token"
        mock_file.assert_called_once_with(jwt_manager.token_file, 'r')

    @patch('src.utils.jwt_utils.Path.exists')
    def test_load_token_file_not_exists(self, mock_exists, jwt_manager):
        """Test de chargement quand le fichier n'existe pas"""
        mock_exists.return_value = False

        token = jwt_manager.load_token()

        assert token is None

    @patch('src.utils.jwt_utils.Path.unlink')
    @patch('src.utils.jwt_utils.Path.exists')
    def test_clear_token_success(self, mock_exists, mock_unlink, jwt_manager):
        """Test de suppression de token réussie"""
        mock_exists.return_value = True

        result = jwt_manager.clear_token()

        assert result is True
        mock_unlink.assert_called_once()

    @patch('src.utils.jwt_utils.Path.exists')
    def test_clear_token_file_not_exists(self, mock_exists, jwt_manager):
        """Test de suppression quand le fichier n'existe pas"""
        mock_exists.return_value = False

        result = jwt_manager.clear_token()

        assert result is True  # Should still return True

    def test_get_current_user_data_no_token(self, jwt_manager):
        """Test récupération données utilisateur sans token"""
        with patch.object(jwt_manager, 'load_token', return_value=None):
            user_data = jwt_manager.get_current_user_data()
            assert user_data is None

    def test_get_current_user_data_valid_token(self, jwt_manager):
        """Test récupération données utilisateur avec token valide"""
        token = jwt_manager.generate_token(
            user_id=456,
            email="user@example.com",
            department="support",
            employee_number="EE789123"
        )

        with patch.object(jwt_manager, 'load_token', return_value=token):
            user_data = jwt_manager.get_current_user_data()

            assert user_data is not None
            assert user_data.get('user_id') == 456
            assert user_data.get('email') == "user@example.com"

    def test_is_authenticated_true(self, jwt_manager):
        """Test d'authentification réussie"""
        token = jwt_manager.generate_token(
            user_id=789,
            email="auth@example.com",
            department="gestion",
            employee_number="EE456789"
        )

        with patch.object(jwt_manager, 'load_token', return_value=token):
            is_auth = jwt_manager.is_authenticated()
            assert is_auth is True

    def test_is_authenticated_false(self, jwt_manager):
        """Test d'authentification échouée"""
        with patch.object(jwt_manager, 'load_token', return_value=None):
            is_auth = jwt_manager.is_authenticated()
            assert is_auth is False

    def test_token_roundtrip(self, jwt_manager):
        """Test complet de génération/sauvegarde/chargement/vérification"""
        # Générer un token
        token = jwt_manager.generate_token(
            user_id=456,
            email="roundtrip@example.com",
            department="commercial",
            employee_number="EE987654"
        )
        assert token is not None

        # Vérifier le token
        payload = jwt_manager.verify_token(token)
        assert payload is not None
        assert payload.get('user_id') == 456

    def test_different_users_different_tokens(self, jwt_manager):
        """Test que différents utilisateurs génèrent des tokens différents"""
        token_1 = jwt_manager.generate_token(
            user_id=1,
            email="user1@example.com",
            department="commercial",
            employee_number="EE111111"
        )
        token_2 = jwt_manager.generate_token(
            user_id=2,
            email="user2@example.com",
            department="support",
            employee_number="EE222222"
        )

        assert token_1 != token_2

        # Vérifier que chaque token contient les bonnes données
        payload_1 = jwt_manager.verify_token(token_1)
        payload_2 = jwt_manager.verify_token(token_2)

        assert payload_1.get('user_id') == 1
        assert payload_2.get('user_id') == 2

    def test_token_payload_structure(self, jwt_manager):
        """Test de la structure du payload du token"""
        token = jwt_manager.generate_token(
            user_id=789,
            email="structure@example.com",
            department="gestion",
            employee_number="EE111222"
        )

        payload = jwt_manager.verify_token(token)

        # Vérifier la structure attendue
        assert 'user_id' in payload
        assert 'email' in payload
        assert 'department' in payload
        assert 'employee_number' in payload
        assert 'exp' in payload  # Expiration
        assert 'iat' in payload  # Issued at

        # Vérifier les valeurs
        assert payload['user_id'] == 789
        assert payload['email'] == "structure@example.com"
        assert payload['department'] == "gestion"
        assert payload['employee_number'] == "EE111222"

        # Vérifier les types
        assert isinstance(payload['user_id'], int)
        assert isinstance(payload['exp'], int)
        assert isinstance(payload['iat'], int)

        # Vérifier que exp > iat
        assert payload['exp'] > payload['iat']
