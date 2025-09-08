"""
Tests simples pour les utilisateurs - Sans mock
"""
import pytest
from src.controllers.user_controller import UserController
from src.models.user import User, Department
from src.utils.validators import ValidationError
from src.utils.auth_utils import AuthorizationError


def test_create_user_admin(db_session, admin_user):
    """Un admin peut créer un utilisateur"""
    controller = UserController(db_session)
    controller.set_current_user(admin_user)

    new_user = controller.create_user(
        full_name="Nouvel Utilisateur",
        email="nouveau@user.com",
        password="Password123!",  # Mot de passe fort
        department=Department.COMMERCIAL.value
    )

    assert new_user.full_name == "Nouvel Utilisateur"
    assert new_user.email == "nouveau@user.com"
    assert new_user.department == Department.COMMERCIAL


def test_create_user_commercial_interdit(db_session, commercial_user):
    """Un commercial ne peut pas créer d'utilisateur"""
    controller = UserController(db_session)
    controller.set_current_user(commercial_user)

    with pytest.raises(AuthorizationError):
        controller.create_user(
            full_name="Utilisateur Interdit",
            email="interdit@user.com",
            password="password123",
            department=Department.SUPPORT
        )


def test_get_all_users(db_session, admin_user, commercial_user, support_user):
    """Récupérer tous les utilisateurs"""
    controller = UserController(db_session)
    controller.set_current_user(admin_user)

    users = controller.get_all_users()

    # Au moins 3 utilisateurs créés
    assert len(users) >= 3
    emails = [u.email for u in users]
    assert "admin@test.com" in emails
    assert "commercial@test.com" in emails
    assert "support@test.com" in emails


def test_get_user_by_id(db_session, admin_user, commercial_user):
    """Récupérer un utilisateur par ID"""
    controller = UserController(db_session)
    controller.set_current_user(admin_user)

    user = controller.get_user_by_id(commercial_user.id)

    assert user.id == commercial_user.id
    assert user.email == "commercial@test.com"


def test_update_user(db_session, admin_user, commercial_user):
    """Mettre à jour un utilisateur"""
    controller = UserController(db_session)
    controller.set_current_user(admin_user)

    updated_user = controller.update_user(
        commercial_user.id,
        full_name="Commercial Modifié"
    )

    assert updated_user.full_name == "Commercial Modifié"
    assert updated_user.email == "commercial@test.com"  # Pas changé


def test_search_users(db_session, admin_user, commercial_user):
    """Rechercher des utilisateurs"""
    controller = UserController(db_session)
    controller.set_current_user(admin_user)

    users = controller.search_users(name="Commercial")

    assert len(users) >= 1
    user_ids = [u.id for u in users]
    assert commercial_user.id in user_ids


def test_delete_user(db_session, admin_user):
    """Supprimer un utilisateur"""
    controller = UserController(db_session)
    controller.set_current_user(admin_user)

    # Créer un utilisateur à supprimer
    user_to_delete = User(
        employee_number="DEL001",  # Ajouter employee_number
        full_name="À Supprimer",
        email="delete@test.com",
        department=Department.SUPPORT
    )
    user_to_delete.set_password("password123")
    db_session.add(user_to_delete)
    db_session.commit()

    user_id = user_to_delete.id

    # Supprimer
    controller.delete_user(user_id)

    # Vérifier qu'il n'existe plus
    deleted_user = controller.get_user_by_id(user_id)
    assert deleted_user is None


def test_create_user_email_invalide(db_session, admin_user):
    """Validation email invalide"""
    controller = UserController(db_session)
    controller.set_current_user(admin_user)

    with pytest.raises(ValidationError):
        controller.create_user(
            full_name="Test User",
            email="email_invalide",  # Email incorrect
            password="password123",
            department=Department.COMMERCIAL.value
        )


def test_create_user_password_court(db_session, admin_user):
    """Validation mot de passe trop court"""
    controller = UserController(db_session)
    controller.set_current_user(admin_user)

    with pytest.raises(ValidationError):
        controller.create_user(
            full_name="Test User",
            email="test@user.com",
            password="123",  # Trop court
            department=Department.COMMERCIAL.value
        )
