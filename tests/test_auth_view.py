import pytest
import tempfile
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.connection import Base
from src.models.user import User, Department
from src.views.auth_view import AuthView
from src.utils.hash_utils import hash_password


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
    """Creer un repertoire temporaire pour les tokens"""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('src.utils.jwt_utils.Path.home') as mock_home:
            mock_home.return_value = temp_dir
            yield temp_dir


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


def test_auth_view_init():
    """Tester l'initialisation de AuthView"""
    with patch('src.views.auth_view.sessionmaker') as mock_sessionmaker:
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)

        auth_view = AuthView()
        assert auth_view.db == mock_session


@patch('getpass.getpass')
@patch('src.views.auth_view.AuthView.get_user_input')
def test_login_command_success(mock_input, mock_getpass, temp_token_dir, test_user):
    """Tester la commande de connexion reussie"""
    mock_input.return_value = "test@epicevents.com"
    mock_getpass.return_value = "TestPass123!"

    with patch('src.views.auth_view.sessionmaker') as mock_sessionmaker:
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        session.add(test_user)
        session.commit()

        mock_sessionmaker.return_value = MagicMock(return_value=session)

        auth_view = AuthView()

        with patch('builtins.print') as mock_print:
            auth_view.login_command()

            # Verifier que les messages de succes sont affiches
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            success_messages = [msg for msg in print_calls if 'Connexion reussie' in msg]
            assert len(success_messages) > 0


@patch('getpass.getpass')
@patch('src.views.auth_view.AuthView.get_user_input')
def test_login_command_invalid_credentials(mock_input, mock_getpass, temp_token_dir, test_user):
    """Tester la commande de connexion avec identifiants invalides"""
    mock_input.return_value = "test@epicevents.com"
    mock_getpass.return_value = "WrongPassword"

    with patch('src.views.auth_view.sessionmaker') as mock_sessionmaker:
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        session.add(test_user)
        session.commit()

        mock_sessionmaker.return_value = MagicMock(return_value=session)

        auth_view = AuthView()

        with patch('builtins.print') as mock_print:
            auth_view.login_command()

            print_calls = [call[0][0] for call in mock_print.call_args_list]
            error_messages = [msg for msg in print_calls if 'ERREUR' in msg]
            assert len(error_messages) > 0


def test_logout_command_not_authenticated(temp_token_dir):
    """Tester la deconnexion sans etre connecte"""
    with patch('src.views.auth_view.sessionmaker') as mock_sessionmaker:
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)

        auth_view = AuthView()

        with patch('builtins.print') as mock_print:
            auth_view.logout_command()

            print_calls = [call[0][0] for call in mock_print.call_args_list]
            info_messages = [msg for msg in print_calls if 'pas connecte' in msg]
            assert len(info_messages) > 0


def test_status_command_not_authenticated(temp_token_dir):
    """Tester la commande status sans etre connecte"""
    with patch('src.views.auth_view.sessionmaker') as mock_sessionmaker:
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)

        auth_view = AuthView()

        with patch('builtins.print') as mock_print:
            auth_view.status_command()

            print_calls = [call[0][0] for call in mock_print.call_args_list]
            status_messages = [msg for msg in print_calls if 'Connecte: NON' in msg]
            assert len(status_messages) > 0


def test_whoami_command_not_authenticated(temp_token_dir):
    """Tester la commande whoami sans etre connecte"""
    with patch('src.views.auth_view.sessionmaker') as mock_sessionmaker:
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)

        auth_view = AuthView()

        with patch('builtins.print') as mock_print:
            auth_view.whoami_command()

            print_calls = [call[0][0] for call in mock_print.call_args_list]
            not_connected_messages = [msg for msg in print_calls if 'Non connecte' in msg]
            assert len(not_connected_messages) > 0
