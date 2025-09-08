"""
Tests pour les utilitaires JWT
Fichier: tests/test_jwt_utils.py
"""
import unittest
from unittest.mock import patch, mock_open
from src.utils.jwt_utils import JWTManager


class TestJWTManager(unittest.TestCase):

    def setUp(self):
        """Setup pour chaque test"""
        self.jwt_manager = JWTManager()

    def test_generate_token_success(self):
        """Test de génération de token JWT réussie"""
        token = self.jwt_manager.generate_token(
            user_id=1,
            email="test@example.com",
            department="COMMERCIAL",
            employee_number="EE123456"
        )

        self.assertIsNotNone(token)
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 50)  # Un JWT fait normalement plus de 50 caractères

    def test_verify_token_success(self):
        """Test de vérification de token JWT valide"""
        token = self.jwt_manager.generate_token(
            user_id=1,
            email="test@example.com",
            department="COMMERCIAL",
            employee_number="EE123456"
        )

        payload = self.jwt_manager.verify_token(token)

        self.assertIsNotNone(payload)
        self.assertEqual(payload['user_id'], 1)
        self.assertEqual(payload['email'], "test@example.com")
        self.assertEqual(payload['department'], "COMMERCIAL")
        self.assertEqual(payload['employee_number'], "EE123456")

    def test_verify_token_invalid(self):
        """Test de vérification de token JWT invalide"""
        invalid_token = "invalid.jwt.token"

        payload = self.jwt_manager.verify_token(invalid_token)

        self.assertIsNone(payload)

    def test_verify_token_malformed(self):
        """Test de vérification de token JWT malformé"""
        malformed_token = "not.a.jwt"

        payload = self.jwt_manager.verify_token(malformed_token)

        self.assertIsNone(payload)

    @patch('src.utils.jwt_utils.os.chmod')
    @patch('src.utils.jwt_utils.json.dump')
    @patch('builtins.open', new_callable=mock_open)
    @patch.object(JWTManager, '_ensure_token_dir')
    def test_save_token_success(self, mock_ensure_dir, mock_file, mock_json_dump, mock_chmod):
        """Test de sauvegarde de token réussie"""
        token = "test.jwt.token"

        result = self.jwt_manager.save_token(token)

        self.assertTrue(result)
        mock_ensure_dir.assert_called_once()
        mock_file.assert_called_once()
        mock_json_dump.assert_called_once()
        mock_chmod.assert_called_once()

    @patch('builtins.open', side_effect=IOError("Permission denied"))
    @patch('pathlib.Path.mkdir')
    def test_save_token_failure(self, mock_mkdir, mock_file):
        """Test de sauvegarde de token échouée"""
        token = "test.jwt.token"

        result = self.jwt_manager.save_token(token)

        self.assertFalse(result)

    @patch('src.utils.jwt_utils.json.load', return_value={'token': 'test.jwt.token'})
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists', return_value=True)
    def test_load_token_success(self, mock_exists, mock_file, mock_json_load):
        """Test de chargement de token réussi"""
        token = self.jwt_manager.load_token()

        self.assertEqual(token, "test.jwt.token")
        mock_file.assert_called_once()
        mock_json_load.assert_called_once()

    @patch('pathlib.Path.exists', return_value=False)
    def test_load_token_file_not_exists(self, mock_exists):
        """Test de chargement de token - fichier inexistant"""
        token = self.jwt_manager.load_token()

        self.assertIsNone(token)

    @patch('builtins.open', side_effect=IOError("Read error"))
    @patch('pathlib.Path.exists', return_value=True)
    def test_load_token_read_error(self, mock_exists, mock_file):
        """Test de chargement de token - erreur de lecture"""
        token = self.jwt_manager.load_token()

        self.assertIsNone(token)

    @patch('pathlib.Path.unlink')
    @patch('pathlib.Path.exists', return_value=True)
    def test_clear_token_success(self, mock_exists, mock_unlink):
        """Test de suppression de token réussie"""
        result = self.jwt_manager.clear_token()

        self.assertTrue(result)
        mock_unlink.assert_called_once()

    @patch('pathlib.Path.exists', return_value=False)
    def test_clear_token_file_not_exists(self, mock_exists):
        """Test de suppression de token - fichier inexistant"""
        result = self.jwt_manager.clear_token()

        self.assertTrue(result)  # Success même si le fichier n'existe pas

    def test_token_expiration(self):
        """Test de l'expiration des tokens"""
        # Créer un token avec expiration très courte
        original_exp = self.jwt_manager.expiration_hours
        self.jwt_manager.expiration_hours = -1  # Expiré

        token = self.jwt_manager.generate_token(
            user_id=1,
            email="test@example.com",
            department="COMMERCIAL",
            employee_number="EE123456"
        )

        # Vérifier que le token expiré retourne None
        payload = self.jwt_manager.verify_token(token)
        self.assertIsNone(payload)

        # Restaurer l'expiration originale
        self.jwt_manager.expiration_hours = original_exp

    @patch('src.utils.jwt_utils.JWTManager.load_token')
    @patch('src.utils.jwt_utils.JWTManager.verify_token')
    def test_is_authenticated_valid_token(self, mock_verify, mock_load):
        """Test d'authentification avec token valide"""
        mock_load.return_value = "valid.jwt.token"
        mock_verify.return_value = {"user_id": 1}

        result = self.jwt_manager.is_authenticated()

        self.assertTrue(result)

    @patch('src.utils.jwt_utils.JWTManager.load_token')
    def test_is_authenticated_no_token(self, mock_load):
        """Test d'authentification sans token"""
        mock_load.return_value = None

        result = self.jwt_manager.is_authenticated()

        self.assertFalse(result)

    @patch('src.utils.jwt_utils.JWTManager.load_token')
    @patch('src.utils.jwt_utils.JWTManager.verify_token')
    def test_get_current_user_data_success(self, mock_verify, mock_load):
        """Test de récupération des données utilisateur"""
        mock_load.return_value = "valid.jwt.token"
        mock_verify.return_value = {
            "user_id": 1,
            "email": "test@example.com",
            "department": "COMMERCIAL"
        }

        data = self.jwt_manager.get_current_user_data()

        self.assertIsNotNone(data)
        self.assertEqual(data["user_id"], 1)
        self.assertEqual(data["email"], "test@example.com")

    @patch('src.utils.jwt_utils.JWTManager.load_token')
    def test_get_current_user_data_no_token(self, mock_load):
        """Test de récupération des données utilisateur sans token"""
        mock_load.return_value = None

        data = self.jwt_manager.get_current_user_data()

        self.assertIsNone(data)


if __name__ == '__main__':
    unittest.main()
