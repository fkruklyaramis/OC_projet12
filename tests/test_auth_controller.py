import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.connection import Base
from src.models.user import User, Department
from src.controllers.auth_controller import AuthController
from src.utils.auth_utils import AuthenticationError, AuthorizationError


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def auth_controller(db_session):
    return AuthController(db_session)


@pytest.fixture
def admin_user(db_session):
    from src.utils.hash_utils import hash_password
    controller = AuthController(db_session)
    admin = User(
        employee_number="EE000001",
        email="admin@epicevents.com",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Admin Test",
        department=Department.GESTION
    )
    db_session.add(admin)
    db_session.commit()
    controller.set_current_user(admin)
    return controller


def test_create_user_success(admin_user):
    """Tester la création d'un utilisateur avec succès"""
    user = admin_user.create_user(
        email="test@epicevents.com",
        password="TestPass123!",
        full_name="Test User",
        department=Department.COMMERCIAL
    )

    assert user.email == "test@epicevents.com"
    assert user.full_name == "Test User"
    assert user.department == Department.COMMERCIAL
    assert user.employee_number.startswith("EE")
    assert len(user.employee_number) == 8


def test_create_user_weak_password(admin_user):
    """Tester la création avec un mot de passe faible"""
    with pytest.raises(ValueError, match="critères de sécurité"):
        admin_user.create_user(
            email="test@epicevents.com",
            password="weak",
            full_name="Test User",
            department=Department.COMMERCIAL
        )


def test_create_user_duplicate_email(admin_user):
    """Tester la création avec un email déjà existant"""
    admin_user.create_user(
        email="test@epicevents.com",
        password="TestPass123!",
        full_name="Test User",
        department=Department.COMMERCIAL
    )

    with pytest.raises(ValueError, match="email est déjà utilisé"):
        admin_user.create_user(
            email="test@epicevents.com",
            password="TestPass456!",
            full_name="Another User",
            department=Department.SUPPORT
        )


def test_unauthorized_user_creation(auth_controller):
    """Tester la création d'utilisateur sans autorisation"""
    with pytest.raises(AuthorizationError):
        auth_controller.create_user(
            email="test@epicevents.com",
            password="TestPass123!",
            full_name="Test User",
            department=Department.COMMERCIAL
        )


def test_authenticate_valid_user(db_session):
    """Tester l'authentification avec des identifiants valides"""
    from src.utils.hash_utils import hash_password

    user = User(
        employee_number="EE000002",
        email="user@epicevents.com",
        hashed_password=hash_password("TestPass123!"),
        full_name="Valid User",
        department=Department.COMMERCIAL
    )
    db_session.add(user)
    db_session.commit()

    auth_controller = AuthController(db_session)
    authenticated_user = auth_controller.authenticate_user(
        "user@epicevents.com",
        "TestPass123!"
    )

    assert authenticated_user.email == "user@epicevents.com"
    assert authenticated_user.full_name == "Valid User"


def test_authenticate_invalid_password(db_session):
    """Tester l'authentification avec un mot de passe invalide"""
    from src.utils.hash_utils import hash_password

    user = User(
        employee_number="EE000003",
        email="user@epicevents.com",
        hashed_password=hash_password("TestPass123!"),
        full_name="Valid User",
        department=Department.COMMERCIAL
    )
    db_session.add(user)
    db_session.commit()

    auth_controller = AuthController(db_session)

    with pytest.raises(AuthenticationError, match="Mot de passe incorrect"):
        auth_controller.authenticate_user("user@epicevents.com", "WrongPass")


def test_authenticate_nonexistent_user(db_session):
    """Tester l'authentification d'un utilisateur inexistant"""
    auth_controller = AuthController(db_session)

    with pytest.raises(AuthenticationError, match="Utilisateur non trouvé"):
        auth_controller.authenticate_user("nonexistent@epicevents.com", "AnyPass123!")


def test_permission_check_admin(admin_user):
    """Tester la vérification des permissions pour admin"""
    assert admin_user.check_permission('create_user') is True
    assert admin_user.check_permission('delete_user') is True
    assert admin_user.check_permission('create_client') is True
    assert admin_user.check_permission('update_contract') is True


def test_permission_check_commercial(admin_user):
    """Tester la vérification des permissions pour commercial"""
    commercial_user = admin_user.create_user(
        email="commercial@epicevents.com",
        password="TestPass123!",
        full_name="Commercial User",
        department=Department.COMMERCIAL
    )

    commercial_controller = AuthController(admin_user.db)
    commercial_controller.set_current_user(commercial_user)

    assert commercial_controller.check_permission('create_client') is True
    assert commercial_controller.check_permission('create_user') is False
    assert commercial_controller.check_permission('delete_user') is False
    assert commercial_controller.check_permission('read_contract') is True


def test_permission_check_support(admin_user):
    """Tester la vérification des permissions pour support"""
    support_user = admin_user.create_user(
        email="support@epicevents.com",
        password="TestPass123!",
        full_name="Support User",
        department=Department.SUPPORT
    )

    support_controller = AuthController(admin_user.db)
    support_controller.set_current_user(support_user)

    assert support_controller.check_permission('create_client') is False
    assert support_controller.check_permission('create_user') is False
    assert support_controller.check_permission('read_event') is True
    assert support_controller.check_permission('update_assigned_event') is True


def test_change_password_success(admin_user):
    """Tester le changement de mot de passe avec succès"""
    user = admin_user.create_user(
        email="changepass@epicevents.com",
        password="OldPass123!",
        full_name="Change Pass User",
        department=Department.COMMERCIAL
    )

    user_controller = AuthController(admin_user.db)
    user_controller.set_current_user(user)

    result = user_controller.change_password(
        user.id,
        "OldPass123!",
        "NewPass456!"
    )

    assert result is True


def test_change_password_wrong_old_password(admin_user):
    """Tester le changement de mot de passe avec ancien mot de passe incorrect"""
    user = admin_user.create_user(
        email="wrongold@epicevents.com",
        password="OldPass123!",
        full_name="Wrong Old User",
        department=Department.COMMERCIAL
    )

    user_controller = AuthController(admin_user.db)
    user_controller.set_current_user(user)

    with pytest.raises(AuthenticationError, match="Ancien mot de passe incorrect"):
        user_controller.change_password(user.id, "WrongOldPass", "NewPass456!")


def test_logout(auth_controller, admin_user):
    """Tester la déconnexion"""
    user = admin_user.create_user(
        email="logout@epicevents.com",
        password="TestPass123!",
        full_name="Logout User",
        department=Department.COMMERCIAL
    )

    auth_controller.set_current_user(user)
    assert auth_controller.current_user is not None

    auth_controller.logout()
    assert auth_controller.current_user is None
