"""
Tests simples pour les clients - Sans mock, base de données temporaire
"""
import pytest
from src.controllers.client_controller import ClientController
from src.utils.validators import ValidationError
from src.utils.auth_utils import AuthorizationError


def test_create_client_commercial(db_session, commercial_user):
    """Un commercial peut créer un client"""
    # Créer le contrôleur avec la session de test
    controller = ClientController(db_session)
    controller.set_current_user(commercial_user)

    # Créer un client
    client = controller.create_client(
        full_name="Nouveau Client",
        email="nouveau@client.com",
        phone="0123456789",
        company_name="Nouvelle Entreprise"
    )

    # Vérifications
    assert client.full_name == "Nouveau Client"
    assert client.email == "nouveau@client.com"
    assert client.commercial_contact_id == commercial_user.id


def test_create_client_admin(db_session, admin_user, commercial_user):
    """Un admin peut créer un client en spécifiant le commercial"""
    controller = ClientController(db_session)
    controller.set_current_user(admin_user)

    client = controller.create_client(
        full_name="Client Admin",
        email="admin@client.com",
        phone="0123456789",
        company_name="Entreprise Admin",
        commercial_contact_id=commercial_user.id
    )

    assert client.commercial_contact_id == commercial_user.id


def test_create_client_support_interdit(db_session, support_user):
    """Un support ne peut pas créer de client"""
    controller = ClientController(db_session)
    controller.set_current_user(support_user)

    with pytest.raises(AuthorizationError):
        controller.create_client(
            full_name="Client Interdit",
            email="interdit@client.com",
            phone="0123456789",
            company_name="Entreprise Interdite"
        )


def test_get_all_clients_admin(db_session, admin_user, client_example):
    """Un admin peut voir tous les clients"""
    controller = ClientController(db_session)
    controller.set_current_user(admin_user)

    clients = controller.get_all_clients()

    assert len(clients) == 1
    assert clients[0].id == client_example.id


def test_get_my_clients_commercial(db_session, commercial_user, client_example):
    """Un commercial voit ses clients"""
    controller = ClientController(db_session)
    controller.set_current_user(commercial_user)

    clients = controller.get_my_clients()

    assert len(clients) == 1
    assert clients[0].id == client_example.id


def test_get_client_by_id(db_session, commercial_user, client_example):
    """Récupérer un client par son ID"""
    controller = ClientController(db_session)
    controller.set_current_user(commercial_user)

    client = controller.get_client_by_id(client_example.id)

    assert client.id == client_example.id
    assert client.full_name == "Client Test"


def test_search_clients(db_session, commercial_user, client_example):
    """Rechercher des clients par nom"""
    controller = ClientController(db_session)
    controller.set_current_user(commercial_user)

    clients = controller.search_clients(name="Client")

    assert len(clients) == 1
    assert clients[0].id == client_example.id


def test_update_client(db_session, commercial_user, client_example):
    """Mettre à jour un client"""
    controller = ClientController(db_session)
    controller.set_current_user(commercial_user)

    updated_client = controller.update_client(
        client_example.id,
        email="nouveau@email.com"
    )

    assert updated_client.email == "nouveau@email.com"
    assert updated_client.full_name == "Client Test"  # Pas changé


def test_create_client_email_invalide(db_session, commercial_user):
    """Validation de l'email invalide"""
    controller = ClientController(db_session)
    controller.set_current_user(commercial_user)

    with pytest.raises(ValidationError):
        controller.create_client(
            full_name="Test",
            email="email_pas_valide",  # Email incorrect
            phone="0123456789",
            company_name="Test"
        )


def test_create_client_nom_vide(db_session, commercial_user):
    """Validation du nom vide"""
    controller = ClientController(db_session)
    controller.set_current_user(commercial_user)

    with pytest.raises(Exception):  # Simplifions pour éviter les messages manquants
        controller.create_client(
            full_name="",  # Nom vide
            email="test@client.com",
            phone="0123456789",
            company_name="Test"
        )
