from typing import List
from sqlalchemy.orm import sessionmaker
from src.database.connection import engine
from src.controllers.client_controller import ClientController
from src.services.auth_service import AuthenticationService
from src.models.client import Client
from src.utils.auth_utils import AuthenticationError, AuthorizationError
from .base_view import BaseView


class ClientView(BaseView):
    """Vue pour la gestion des clients - Pattern MVC"""

    def __init__(self):
        super().__init__()
        SessionLocal = sessionmaker(bind=engine)
        self.db = SessionLocal()
        self.client_controller = ClientController(self.db)
        self.auth_service = AuthenticationService(self.db)

        current_user = self.auth_service.get_current_user()
        if current_user:
            self.client_controller.set_current_user(current_user)

    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()

    def create_client_command(self):
        """Creer un nouveau client"""
        try:
            current_user = self.auth_service.require_authentication()
            self.client_controller.set_current_user(current_user)

            self.display_info("=== CREATION D'UN NOUVEAU CLIENT ===")

            full_name = self.get_user_input("Nom complet")
            email = self.get_user_input("Email")
            phone = self.get_user_input("Telephone")
            company_name = self.get_user_input("Nom de l'entreprise")

            client = self.client_controller.create_client(
                full_name=full_name,
                email=email,
                phone=phone,
                company_name=company_name
            )

            if client:
                self.display_success(f"Client cree avec succes! ID: {client.id}")
                self._display_client_details(client)
            else:
                self.display_error("Echec de la creation du client")

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(f"Erreur d'autorisation: {e}")
        except ValueError as e:
            self.display_error(f"Erreur de validation: {e}")
        except Exception as e:
            self.display_error(f"Erreur: {e}")

    def list_clients_command(self, my_clients: bool = False):
        """Lister les clients"""
        try:
            current_user = self.auth_service.require_authentication()
            self.client_controller.set_current_user(current_user)

            if my_clients and current_user.is_commercial:
                clients = self.client_controller.get_my_clients()
                title = "=== MES CLIENTS ==="
            else:
                clients = self.client_controller.get_all_clients()
                title = "=== TOUS LES CLIENTS ==="

            self.display_info(title)

            if not clients:
                self.display_info("Aucun client trouve")
                return

            self._display_clients_table(clients)

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(f"Erreur d'autorisation: {e}")
        except Exception as e:
            self.display_error(f"Erreur: {e}")

    def update_client_command(self, client_id: int):
        """Modifier un client"""
        try:
            current_user = self.auth_service.require_authentication()
            self.client_controller.set_current_user(current_user)

            client = self.client_controller.get_client_by_id(client_id)
            if not client:
                self.display_error("Client non trouve")
                return

            self.display_info("=== MODIFICATION DU CLIENT ===")
            self._display_client_details(client)

            updates = {}

            new_name = self.get_user_input(f"Nom complet [{client.full_name}]")
            if new_name:
                updates['full_name'] = new_name

            new_email = self.get_user_input(f"Email [{client.email}]")
            if new_email:
                updates['email'] = new_email

            new_phone = self.get_user_input(f"Telephone [{client.phone}]")
            if new_phone:
                updates['phone'] = new_phone

            new_company = self.get_user_input(f"Entreprise [{client.company_name}]")
            if new_company:
                updates['company_name'] = new_company

            if not updates:
                self.display_info("Aucune modification apportee")
                return

            updated_client = self.client_controller.update_client(client_id, **updates)
            if updated_client:
                self.display_success("Client modifie avec succes!")
                self._display_client_details(updated_client)
            else:
                self.display_error("Echec de la modification")

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(f"Erreur d'autorisation: {e}")
        except Exception as e:
            self.display_error(f"Erreur: {e}")

    def search_clients_command(self):
        """Rechercher des clients"""
        try:
            current_user = self.auth_service.require_authentication()
            self.client_controller.set_current_user(current_user)

            self.display_info("=== RECHERCHE DE CLIENTS ===")

            criteria = {}

            company_search = self.get_user_input("Nom d'entreprise (optionnel)")
            if company_search:
                criteria['company_name'] = company_search

            name_search = self.get_user_input("Nom de personne (optionnel)")
            if name_search:
                criteria['full_name'] = name_search

            email_search = self.get_user_input("Email (optionnel)")
            if email_search:
                criteria['email'] = email_search

            if not criteria:
                self.display_info("Aucun critere de recherche fourni")
                return

            clients = self.client_controller.search_clients(**criteria)

            if clients:
                self.display_success(f"{len(clients)} client(s) trouve(s)")
                self._display_clients_table(clients)
            else:
                self.display_info("Aucun client correspondant trouve")

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(f"Erreur d'autorisation: {e}")
        except Exception as e:
            self.display_error(f"Erreur: {e}")

    def _display_client_details(self, client: Client):
        """Afficher les details d'un client"""
        print(f"\nID: {client.id}")
        print(f"Nom: {client.full_name}")
        print(f"Email: {client.email}")
        print(f"Telephone: {client.phone}")
        print(f"Entreprise: {client.company_name}")
        print(f"Commercial: {client.commercial_contact.full_name}")
        print(f"Cree le: {client.created_at.strftime('%Y-%m-%d %H:%M')}")
        if client.updated_at:
            print(f"Modifie le: {client.updated_at.strftime('%Y-%m-%d %H:%M')}")

    def _display_clients_table(self, clients: List[Client]):
        """Afficher les clients sous forme de tableau"""
        header = f"{'ID':<5} {'Nom':<20} {'Entreprise':<20} {'Email':<30} {'Commercial':<20}"
        print(header)
        print("-" * len(header))

        for client in clients:
            commercial_name = (client.commercial_contact.full_name
                               if client.commercial_contact else "N/A")
            print(f"{client.id:<5} {client.full_name[:19]:<20} "
                  f"{client.company_name[:19]:<20} {client.email[:29]:<30} "
                  f"{commercial_name[:19]:<20}")
