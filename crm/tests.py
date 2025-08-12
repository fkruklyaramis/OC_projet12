"""Tests pour l'authentification et les permissions"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from .auth import AuthService, PermissionService

User = get_user_model()


class AuthTest(TestCase):
    """Tests simples pour l'authentification et permissions"""

    def test_create_and_authenticate_user(self):
        """Test création et authentification"""
        # Créer un utilisateur
        user = AuthService.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            role="COMMERCIAL",
            employee_number="EMP001"
        )

        # Vérifier la création
        self.assertEqual(user.role, "COMMERCIAL")
        self.assertEqual(user.employee_number, "EMP001")

        # Tester l'authentification
        auth_user = AuthService.authenticate_user("testuser", "testpass123")
        self.assertEqual(auth_user, user)

        # Tester avec mauvais mot de passe
        auth_user = AuthService.authenticate_user("testuser", "wrongpass")
        self.assertIsNone(auth_user)

    def test_permissions(self):
        """Test des permissions"""
        commercial = AuthService.create_user(
            "commercial", "c@test.com", "pass123", "COMMERCIAL", "EMP001"
        )
        support = AuthService.create_user(
            "support", "s@test.com", "pass123", "SUPPORT", "EMP002"
        )
        gestion = AuthService.create_user(
            "gestion", "g@test.com", "pass123", "GESTION", "EMP003"
        )

        # Tests permissions clients
        self.assertTrue(PermissionService.can_create_clients(commercial))
        self.assertFalse(PermissionService.can_create_clients(support))
        self.assertTrue(PermissionService.can_create_clients(gestion))

        # Tests permissions contrats
        self.assertFalse(PermissionService.can_manage_contracts(commercial))
        self.assertFalse(PermissionService.can_manage_contracts(support))
        self.assertTrue(PermissionService.can_manage_contracts(gestion))

        # Tests permissions support
        self.assertFalse(PermissionService.can_assign_support(commercial))
        self.assertFalse(PermissionService.can_assign_support(support))
        self.assertTrue(PermissionService.can_assign_support(gestion))
