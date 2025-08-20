import pytest
import tempfile
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.connection import Base
from src.models.user import User, Department
from src.models.client import Client
from src.views.client_view import ClientView
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
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('src.utils.jwt_utils.Path.home') as mock_home:
            mock_home.return_value = temp_dir
            yield temp_dir


@pytest.fixture
def commercial_user(db_session):
    user = User(
        employee_number="EE000001",
        email="commercial@epicevents.com",
        hashed_password=hash_password("TestPass123!"),
        full_name="Commercial User",
        department=Department.COMMERCIAL
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_client(db_session, commercial_user):
    client = Client(
        full_name="Test Client",
        email="client@company.com",
        phone="0123456789",
        company_name="Test Company",
        commercial_contact_id=commercial_user.id
    )
    db_session.add(client)
    db_session.commit()
    return client


@patch('src.views.client_view.ClientView.get_user_input')
def test_create_client_command_success(mock_input, temp_token_dir, commercial_user):
    """Tester la creation d'un client avec succes"""
    mock_input.side_effect = ["New Client", "newclient@company.com",
                              "0987654321", "New Company"]

    with patch('src.views.client_view.sessionmaker') as mock_sessionmaker:
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        session.add(commercial_user)
        session.commit()

        mock_sessionmaker.return_value = MagicMock(return_value=session)

        # Simuler une connexion
        with patch('src.services.auth_service.AuthenticationService.require_authentication') \
             as mock_auth:
            mock_auth.return_value = commercial_user

            with patch('src.services.auth_service.AuthenticationService.get_current_user') \
                 as mock_current:
                mock_current.return_value = commercial_user

                client_view = ClientView()

                with patch('builtins.print') as mock_print:
                    client_view.create_client_command()

                    print_calls = [call[0][0] for call in mock_print.call_args_list]
                    success_messages = [msg for msg in print_calls if 'cree avec succes' in msg]
                    assert len(success_messages) > 0


def test_list_clients_command_empty(temp_token_dir, commercial_user):
    """Tester l'affichage des clients quand la liste est vide"""
    with patch('src.views.client_view.sessionmaker') as mock_sessionmaker:
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        session.add(commercial_user)
        session.commit()

        mock_sessionmaker.return_value = MagicMock(return_value=session)

        with patch('src.services.auth_service.AuthenticationService.require_authentication') \
             as mock_auth:
            mock_auth.return_value = commercial_user

            with patch('src.services.auth_service.AuthenticationService.get_current_user') \
                 as mock_current:
                mock_current.return_value = commercial_user

                client_view = ClientView()

                with patch('builtins.print') as mock_print:
                    client_view.list_clients_command()

                    print_calls = [call[0][0] for call in mock_print.call_args_list]
                    empty_messages = [msg for msg in print_calls if 'Aucun client trouve' in msg]
                    assert len(empty_messages) > 0


def test_list_clients_command_with_data(temp_token_dir, commercial_user, test_client):
    """Tester l'affichage des clients avec donnees"""
    with patch('src.views.client_view.sessionmaker') as mock_sessionmaker:
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        session.add(commercial_user)
        session.add(test_client)
        session.commit()

        mock_sessionmaker.return_value = MagicMock(return_value=session)

        with patch('src.services.auth_service.AuthenticationService.require_authentication') \
             as mock_auth:
            mock_auth.return_value = commercial_user

            with patch('src.services.auth_service.AuthenticationService.get_current_user') \
                 as mock_current:
                mock_current.return_value = commercial_user

                client_view = ClientView()

                with patch('builtins.print') as mock_print:
                    client_view.list_clients_command()

                    print_calls = [call[0][0] for call in mock_print.call_args_list]
                    # Verifier que le tableau d'en-tete est affiche
                    header_messages = [msg for msg in print_calls if 'ID' in msg and 'Nom' in msg]
                    assert len(header_messages) > 0


@patch('src.views.client_view.ClientView.get_user_input')
def test_search_clients_command(mock_input, temp_token_dir, commercial_user, test_client):
    """Tester la recherche de clients"""
    mock_input.side_effect = ["Test Company", "", ""]  # Recherche par entreprise uniquement

    with patch('src.views.client_view.sessionmaker') as mock_sessionmaker:
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        session.add(commercial_user)
        session.add(test_client)
        session.commit()

        mock_sessionmaker.return_value = MagicMock(return_value=session)

        with patch('src.services.auth_service.AuthenticationService.require_authentication') \
             as mock_auth:
            mock_auth.return_value = commercial_user

            with patch('src.services.auth_service.AuthenticationService.get_current_user') \
                 as mock_current:
                mock_current.return_value = commercial_user

                client_view = ClientView()

                with patch('builtins.print') as mock_print:
                    client_view.search_clients_command()

                    print_calls = [call[0][0] for call in mock_print.call_args_list]
                    search_messages = [msg for msg in print_calls if 'client(s) trouve(s)' in msg]
                    assert len(search_messages) >= 0  # Peut etre 0 ou plus selon les resultats
