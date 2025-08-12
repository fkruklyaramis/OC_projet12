"""Tests pour l'authentification et les permissions avec pytest"""
import pytest
import tempfile
from unittest.mock import patch
from django.contrib.auth import get_user_model
from .auth import AuthService, PermissionService
from .jwt_auth import JWTAuthService

User = get_user_model()


@pytest.mark.django_db
class TestAuth:
    """Tests pour l'authentification avec tous les éléments d'identification"""

    def test_create_user_with_all_required_fields(self):
        """Test création d'utilisateur avec tous les champs obligatoires"""
        user = AuthService.create_user(
            username="john_doe",
            email="john@epicevents.com",
            password="motdepasse123",
            role="COMMERCIAL",
            employee_number="EMP001",
            first_name="John",
            last_name="Doe"
        )

        assert user.employee_number == "EMP001"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.email == "john@epicevents.com"
        assert user.role == "COMMERCIAL"
        assert user.full_name == "John Doe"

    def test_authentication_success(self):
        """Test d'authentification réussie"""
        AuthService.create_user(
            "testuser", "test@test.com", "password123", "COMMERCIAL", "EMP001", "Test", "User"
        )

        user = AuthService.authenticate_user("testuser", "password123")
        assert user is not None
        assert user.username == "testuser"

    def test_authentication_failure(self):
        """Test d'authentification échouée"""
        AuthService.create_user(
            "testuser", "test@test.com", "password123", "COMMERCIAL", "EMP001", "Test", "User"
        )

        user = AuthService.authenticate_user("testuser", "wrongpassword")
        assert user is None


@pytest.mark.django_db
class TestJWTAuth:
    """Tests pour l'authentification JWT"""

    @pytest.fixture
    def test_user(self):
        """Fixture pour créer un utilisateur de test"""
        return AuthService.create_user(
            "jwt_user", "jwt@test.com", "password123", "COMMERCIAL", "EMP001", "JWT", "User"
        )

    def test_jwt_login_success(self, test_user):
        """Test de connexion JWT réussie"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            with patch.object(JWTAuthService, 'TOKEN_FILE', tmp.name):
                token, message = JWTAuthService.login("jwt_user", "password123")

                assert token is not None
                assert "Connexion réussie" in message
                assert JWTAuthService.is_authenticated()

    def test_jwt_login_failure(self, test_user):
        """Test de connexion JWT échouée"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            with patch.object(JWTAuthService, 'TOKEN_FILE', tmp.name):
                token, message = JWTAuthService.login("jwt_user", "wrongpassword")

                assert token is None
                assert "Identifiants invalides" in message
                assert not JWTAuthService.is_authenticated()

    def test_jwt_get_current_user(self, test_user):
        """Test récupération utilisateur actuel"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            with patch.object(JWTAuthService, 'TOKEN_FILE', tmp.name):
                JWTAuthService.login("jwt_user", "password123")

                user, message = JWTAuthService.get_current_user()
                assert user is not None
                assert user.username == "jwt_user"
                assert "Session valide" in message

    def test_jwt_logout(self, test_user):
        """Test de déconnexion JWT"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            with patch.object(JWTAuthService, 'TOKEN_FILE', tmp.name):
                JWTAuthService.login("jwt_user", "password123")
                success, message = JWTAuthService.logout()

                assert success
                assert "Déconnexion réussie" in message
                assert not JWTAuthService.is_authenticated()

    def test_jwt_token_info(self, test_user):
        """Test récupération d'informations du token"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            with patch.object(JWTAuthService, 'TOKEN_FILE', tmp.name):
                JWTAuthService.login("jwt_user", "password123")

                token_info = JWTAuthService.get_token_info()
                assert token_info is not None
                assert token_info['username'] == "jwt_user"
                assert token_info['role'] == "COMMERCIAL"

    def test_jwt_permission_check(self, test_user):
        """Test de vérification des permissions via JWT"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            with patch.object(JWTAuthService, 'TOKEN_FILE', tmp.name):
                JWTAuthService.login("jwt_user", "password123")

                has_perm, message = JWTAuthService.check_permission("can_create_clients")
                assert has_perm
                assert "accordée" in message

                has_perm, message = JWTAuthService.check_permission("can_create_contracts")
                assert not has_perm
                assert "refusée" in message

    def test_jwt_signature_consistency(self, test_user):
        """Test de cohérence de signature JWT"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            with patch.object(JWTAuthService, 'TOKEN_FILE', tmp.name):
                # Connexion et vérification immediate
                token, message = JWTAuthService.login("jwt_user", "password123")
                assert token is not None

                # Vérification que le token peut être décodé immédiatement
                user, user_message = JWTAuthService.get_current_user()
                assert user is not None
                assert user.username == "jwt_user"

    def test_jwt_token_expiration_handling(self, test_user):
        """Test de gestion de l'expiration des tokens"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            with patch.object(JWTAuthService, 'TOKEN_FILE', tmp.name):
                with patch.object(JWTAuthService, 'JWT_EXPIRATION_HOURS', -1):
                    JWTAuthService.login("jwt_user", "password123")

                    user, message = JWTAuthService.get_current_user()
                    assert user is None
                    assert "expirée" in message


@pytest.mark.django_db
class TestPermissions:
    """Tests pour les permissions selon le département"""

    @pytest.fixture
    def users(self):
        """Fixture pour créer des utilisateurs de test"""
        commercial = AuthService.create_user(
            "commercial", "c@test.com", "pass123", "COMMERCIAL", "EMP001", "Com", "Mercial"
        )
        support = AuthService.create_user(
            "support", "s@test.com", "pass123", "SUPPORT", "EMP002", "Sup", "Port"
        )
        gestion = AuthService.create_user(
            "gestion", "g@test.com", "pass123", "GESTION", "EMP003", "Ges", "Tion"
        )
        return {
            'commercial': commercial,
            'support': support,
            'gestion': gestion
        }

    def test_client_permissions(self, users):
        """Test des permissions pour les clients"""
        assert PermissionService.can_create_clients(users['commercial']) is True
        assert PermissionService.can_create_clients(users['support']) is False
        assert PermissionService.can_create_clients(users['gestion']) is True

    def test_contract_permissions(self, users):
        """Test des permissions pour les contrats"""
        assert PermissionService.can_create_contracts(users['commercial']) is False
        assert PermissionService.can_create_contracts(users['support']) is False
        assert PermissionService.can_create_contracts(users['gestion']) is True

    @pytest.mark.parametrize("role,expected_permissions", [
        ('COMMERCIAL', ['view_all_data', 'create_clients', 'update_own_clients',
                        'update_own_contracts', 'create_events']),
        ('SUPPORT', ['view_all_data', 'update_own_events']),
        ('GESTION', ['view_all_data', 'create_clients', 'update_all_clients',
                     'create_contracts', 'update_all_contracts', 'create_events',
                     'assign_support', 'update_all_events', 'manage_users'])
    ])
    def test_permissions_by_role(self, role, expected_permissions):
        """Test paramétré des permissions par rôle"""
        user = AuthService.create_user(
            f"user_{role.lower()}", f"{role.lower()}@test.com", "pass123",
            role, f"EMP_{role}", "Test", "User"
        )

        user_permissions = PermissionService.get_user_permissions(user)

        for perm in expected_permissions:
            assert perm in user_permissions
