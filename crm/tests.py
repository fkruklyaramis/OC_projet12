"""Tests pour l'authentification et les permissions avec pytest"""
import pytest
from django.contrib.auth import get_user_model
from .auth import AuthService, PermissionService

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

        # Vérifier tous les éléments d'identification
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
