import pytest
import tempfile
from unittest.mock import patch
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.connection import Base
from src.models.user import User, Department
from src.services.auth_service import AuthenticationService
from src.utils.jwt_utils import JWTManager
from src.utils.hash_utils import hash_password
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
def temp_token_dir():
    """Créer un répertoire temporaire pour les tokens"""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('src.utils.jwt_utils.Path.home') as mock_home:
            mock_home.return_value = temp_dir
            yield temp_dir


@pytest.fixture
def auth_service(db_session, temp_token_dir):
    return AuthenticationService(db_session)


@pytest.fixture
def test_user(db_session):
    user = User(
        employee_number="EE000001",
        email="test@epicevents.com",
        hashed_password=hash_password("TestPass123!"),
        full_name="Test User",
        department=Department.COMMERCIAL
    )
    db_session.add(user)
    db_session.commit()
    return user


def test_jwt_manager_generate_token():
    """Tester la génération de token JWT"""
    jwt_manager = JWTManager()
    token = jwt_manager.generate_token(
        user_id=1,
        email="test@example.com",
        department="commercial",
        employee_number="EE000001"
    )

    assert isinstance(token, str)
    assert len(token) > 0


def test_jwt_manager_verify_valid_token():
    """Tester la vérification d'un token valide"""
    jwt_manager = JWTManager()
    token = jwt_manager.generate_token(
        user_id=1,
        email="test@example.com",
        department="commercial",
        employee_number="EE000001"
    )

    payload = jwt_manager.verify_token(token)
    assert payload is not None
    assert payload['user_id'] == 1
    assert payload['email'] == "test@example.com"
    assert payload['department'] == "commercial"


def test_jwt_manager_verify_expired_token():
    """Tester la vérification d'un token expiré"""
    jwt_manager = JWTManager()

    # Créer un token déjà expiré
    import jwt
    payload = {
        'user_id': 1,
        'email': "test@example.com",
        'department': "commercial",
        'employee_number': "EE000001",
        'exp': datetime.now(timezone.utc) - timedelta(hours=1),
        'iat': datetime.now(timezone.utc) - timedelta(hours=2)
    }
    expired_token = jwt.encode(payload, jwt_manager.secret_key,
                               algorithm=jwt_manager.algorithm)

    result = jwt_manager.verify_token(expired_token)
    assert result is None


def test_jwt_manager_save_and_load_token(temp_token_dir):
    """Tester la sauvegarde et le chargement de token"""
    jwt_manager = JWTManager()
    test_token = "test_token_value"

    # Sauvegarder le token
    success = jwt_manager.save_token(test_token)
    assert success is True

    # Charger le token
    loaded_token = jwt_manager.load_token()
    assert loaded_token == test_token


def test_auth_service_login_success(auth_service, test_user):
    """Tester la connexion réussie avec génération de token"""
    user = auth_service.login("test@epicevents.com", "TestPass123!")

    assert user is not None
    assert user.email == "test@epicevents.com"
    assert auth_service.is_authenticated() is True


def test_auth_service_login_invalid_credentials(auth_service, test_user):
    """Tester la connexion avec des identifiants invalides"""
    with pytest.raises(AuthenticationError):
        auth_service.login("test@epicevents.com", "WrongPassword")


def test_auth_service_get_current_user(auth_service, test_user):
    """Tester la récupération de l'utilisateur actuel"""
    # Se connecter d'abord
    auth_service.login("test@epicevents.com", "TestPass123!")

    # Récupérer l'utilisateur actuel
    current_user = auth_service.get_current_user()
    assert current_user is not None
    assert current_user.email == "test@epicevents.com"
    assert current_user.id == test_user.id


def test_auth_service_logout(auth_service, test_user):
    """Tester la déconnexion"""
    # Se connecter d'abord
    auth_service.login("test@epicevents.com", "TestPass123!")
    assert auth_service.is_authenticated() is True

    # Se déconnecter
    logout_success = auth_service.logout()
    assert logout_success is True
    assert auth_service.is_authenticated() is False
    assert auth_service.get_current_user() is None


def test_auth_service_check_permission(auth_service, test_user):
    """Tester la vérification des permissions"""
    # Se connecter
    auth_service.login("test@epicevents.com", "TestPass123!")

    # Tester permissions commerciales
    assert auth_service.check_permission('create_client') is True
    assert auth_service.check_permission('create_user') is False


def test_auth_service_require_authentication_success(auth_service, test_user):
    """Tester l'exigence d'authentification - cas de succès"""
    auth_service.login("test@epicevents.com", "TestPass123!")

    user = auth_service.require_authentication()
    assert user is not None
    assert user.email == "test@epicevents.com"


def test_auth_service_require_authentication_failure(auth_service):
    """Tester l'exigence d'authentification - cas d'échec"""
    with pytest.raises(AuthenticationError, match="Vous devez être connecté"):
        auth_service.require_authentication()


def test_auth_service_require_permission_success(auth_service, test_user):
    """Tester l'exigence de permission - cas de succès"""
    auth_service.login("test@epicevents.com", "TestPass123!")

    user = auth_service.require_permission('create_client')
    assert user is not None
    assert user.email == "test@epicevents.com"


def test_auth_service_require_permission_failure(auth_service, test_user):
    """Tester l'exigence de permission - cas d'échec"""
    auth_service.login("test@epicevents.com", "TestPass123!")

    with pytest.raises(AuthorizationError, match="Permission requise: create_user"):
        auth_service.require_permission('create_user')


def test_token_persistence_across_sessions(db_session, temp_token_dir, test_user):
    """Tester la persistance du token entre sessions"""
    # Session 1: Se connecter
    auth_service1 = AuthenticationService(db_session)
    auth_service1.login("test@epicevents.com", "TestPass123!")
    assert auth_service1.is_authenticated() is True

    # Session 2: Vérifier que l'authentification persiste
    auth_service2 = AuthenticationService(db_session)
    assert auth_service2.is_authenticated() is True

    current_user = auth_service2.get_current_user()
    assert current_user is not None
    assert current_user.email == "test@epicevents.com"
