"""
Tests pour les contrôleurs utilisateur
Fichier: src/tests/test_user_controller.py
"""

import pytest
from unittest.mock import patch
from src.controllers.user_controller import UserController
from src.models.user import Department
from src.utils.auth_utils import AuthorizationError
from src.utils.validators import ValidationError


class TestUserController:
    """Tests pour le contrôleur des utilisateurs"""

    def test_create_user_success(self, test_db, test_user):
        """Test de création d'utilisateur réussie"""
        controller = UserController(test_db)
        controller.current_user = test_user  # Utilisateur de gestion

        # Mock des permissions pour autoriser la création d'utilisateur
        with patch.object(controller.permission_checker, 'has_permission', return_value=True):
            new_user = controller.create_user(
                email="newuser@test.com",
                password="NewPassword123!",
                full_name="New User",
                department="commercial"
            )

        assert new_user is not None
        assert new_user.email == "newuser@test.com"
        assert new_user.full_name == "New User"
        assert new_user.department == Department.COMMERCIAL
        assert new_user.employee_number.startswith("EE")

    def test_create_user_unauthorized(self, test_db, test_commercial):
        """Test de création d'utilisateur sans autorisation"""
        controller = UserController(test_db)
        controller.current_user = test_commercial  # Commercial n'a pas le droit

        with pytest.raises(AuthorizationError):
            controller.create_user(
                email="newuser@test.com",
                password="NewPassword123!",
                full_name="New User",
                department="commercial"
            )

    def test_create_user_invalid_email(self, test_db, test_user):
        """Test de création d'utilisateur avec email invalide"""
        controller = UserController(test_db)
        controller.current_user = test_user

        with pytest.raises(ValidationError):
            controller.create_user(
                email="invalid-email",
                password="Password123!",
                full_name="Test User",
                department="commercial"
            )

    def test_create_user_weak_password(self, test_db, test_user):
        """Test de création d'utilisateur avec mot de passe faible"""
        controller = UserController(test_db)
        controller.current_user = test_user

        with pytest.raises(ValidationError):
            controller.create_user(
                email="test@example.com",
                password="weak",
                full_name="Test User",
                department="commercial"
            )

    def test_create_user_duplicate_email(self, test_db, test_user):
        """Test de création d'utilisateur avec email existant"""
        controller = UserController(test_db)
        controller.current_user = test_user

        with pytest.raises(ValidationError):
            controller.create_user(
                email=test_user.email,  # Email déjà existant
                password="Password123!",
                full_name="Test User",
                department="commercial"
            )

    def test_get_all_users_success(self, test_db, test_user, test_commercial, test_support):
        """Test de récupération de tous les utilisateurs"""
        controller = UserController(test_db)
        controller.current_user = test_user  # Utilisateur de gestion

        users = controller.get_all_users()

        assert len(users) >= 3  # Au moins les 3 utilisateurs de test
        user_emails = [user.email for user in users]
        assert test_user.email in user_emails
        assert test_commercial.email in user_emails
        assert test_support.email in user_emails

    def test_get_all_users_unauthorized(self, test_db, test_commercial):
        """Test de récupération des utilisateurs sans autorisation"""
        controller = UserController(test_db)
        controller.current_user = test_commercial  # Commercial n'a pas le droit

        with pytest.raises(AuthorizationError):
            controller.get_all_users()

    def test_get_all_users_by_department(self, test_db, test_user, test_commercial, test_support):
        """Test de récupération des utilisateurs par département"""
        controller = UserController(test_db)
        controller.current_user = test_user

        commercial_users = controller.get_all_users(department="commercial")

        assert len(commercial_users) >= 1
        for user in commercial_users:
            assert user.department == Department.COMMERCIAL

    def test_get_user_by_id_success(self, test_db, test_user, test_commercial):
        """Test de récupération d'utilisateur par ID"""
        controller = UserController(test_db)
        controller.current_user = test_user

        found_user = controller.get_user_by_id(test_commercial.id)

        assert found_user is not None
        assert found_user.id == test_commercial.id
        assert found_user.email == test_commercial.email

    def test_get_user_by_id_not_found(self, test_db, test_user):
        """Test de récupération d'utilisateur inexistant"""
        controller = UserController(test_db)
        controller.current_user = test_user

        found_user = controller.get_user_by_id(99999)

        assert found_user is None

    def test_update_user_success(self, test_db, test_user, test_commercial):
        """Test de modification d'utilisateur réussie"""
        controller = UserController(test_db)
        controller.current_user = test_user

        original_name = test_commercial.full_name
        new_name = "Updated Commercial Name"

        # Mock des permissions pour autoriser la mise à jour
        with patch.object(controller.permission_checker, 'has_permission', return_value=True):
            updated_user = controller.update_user(
                test_commercial.id,
                full_name=new_name
            )

        assert updated_user is not None
        assert updated_user.full_name == new_name
        assert updated_user.full_name != original_name

    def test_update_user_unauthorized(self, test_db, test_commercial, test_support):
        """Test de modification d'utilisateur sans autorisation"""
        controller = UserController(test_db)
        controller.current_user = test_commercial  # Commercial n'a pas le droit

        with pytest.raises(AuthorizationError):
            controller.update_user(
                test_support.id,
                full_name="New Name"
            )

    def test_delete_user_success(self, test_db, test_user, test_commercial):
        """Test de suppression d'utilisateur réussie"""
        controller = UserController(test_db)
        controller.current_user = test_user

        user_id = test_commercial.id

        result = controller.delete_user(user_id)

        assert result is True

        # Vérifier que l'utilisateur a été supprimé
        deleted_user = controller.get_user_by_id(user_id)
        assert deleted_user is None

    def test_delete_user_unauthorized(self, test_db, test_commercial, test_support):
        """Test de suppression d'utilisateur sans autorisation"""
        controller = UserController(test_db)
        controller.current_user = test_commercial  # Commercial n'a pas le droit

        with pytest.raises(AuthorizationError):
            controller.delete_user(test_support.id)
