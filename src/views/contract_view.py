from typing import List
from sqlalchemy.orm import sessionmaker
from src.database.connection import engine
from src.controllers.contract_controller import ContractController
from src.services.auth_service import AuthenticationService
from src.models.contract import Contract, ContractStatus
from src.utils.auth_utils import AuthenticationError, AuthorizationError
from .base_view import BaseView


class ContractView(BaseView):
    """Vue pour la gestion des contrats - Pattern MVC"""

    def __init__(self):
        super().__init__()
        SessionLocal = sessionmaker(bind=engine)
        self.db = SessionLocal()
        self.contract_controller = ContractController(self.db)
        self.auth_service = AuthenticationService(self.db)
        
        current_user = self.auth_service.get_current_user()
        if current_user:
            self.contract_controller.set_current_user(current_user)

    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()

    def list_all_contracts_command(self):
        """Lister tous les contrats"""
        try:
            current_user = self.auth_service.require_authentication()
            self.contract_controller.set_current_user(current_user)

            contracts = self.contract_controller.get_all_contracts()
            
            self.display_info("=== TOUS LES CONTRATS ===")
            
            if not contracts:
                self.display_info("Aucun contrat trouve")
                return

            self._display_contracts_table(contracts)

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(f"Erreur d'autorisation: {e}")
        except Exception as e:
            self.display_error(f"Erreur: {e}")

    def list_my_contracts_command(self):
        """Lister mes contrats (commerciaux seulement)"""
        try:
            current_user = self.auth_service.require_authentication()
            self.contract_controller.set_current_user(current_user)

            if not current_user.is_commercial:
                self.display_error("Cette commande est reservee aux commerciaux")
                return

            contracts = self.contract_controller.get_my_contracts()
            
            self.display_info("=== MES CONTRATS ===")
            
            if not contracts:
                self.display_info("Aucun contrat trouve")
                return

            self._display_contracts_table(contracts)

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(f"Erreur d'autorisation: {e}")
        except Exception as e:
            self.display_error(f"Erreur: {e}")

    def list_unsigned_contracts_command(self):
        """Lister les contrats non signes"""
        try:
            current_user = self.auth_service.require_authentication()
            self.contract_controller.set_current_user(current_user)

            contracts = self.contract_controller.get_unsigned_contracts()
            
            self.display_info("=== CONTRATS NON SIGNES ===")
            
            if not contracts:
                self.display_info("Aucun contrat non signe trouve")
                return

            self._display_contracts_table(contracts)

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(f"Erreur d'autorisation: {e}")
        except Exception as e:
            self.display_error(f"Erreur: {e}")

    def list_unpaid_contracts_command(self):
        """Lister les contrats avec des montants dus"""
        try:
            current_user = self.auth_service.require_authentication()
            self.contract_controller.set_current_user(current_user)

            contracts = self.contract_controller.get_unpaid_contracts()
            
            self.display_info("=== CONTRATS AVEC MONTANTS DUS ===")
            
            if not contracts:
                self.display_info("Aucun contrat avec montant du trouve")
                return

            self._display_contracts_table(contracts)

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(f"Erreur d'autorisation: {e}")
        except Exception as e:
            self.display_error(f"Erreur: {e}")

    def view_contract_command(self, contract_id: int):
        """Afficher les details d'un contrat"""
        try:
            current_user = self.auth_service.require_authentication()
            self.contract_controller.set_current_user(current_user)

            contract = self.contract_controller.get_contract_by_id(contract_id)
            if not contract:
                self.display_error("Contrat non trouve")
                return

            self._display_contract_details(contract)

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(f"Erreur d'autorisation: {e}")
        except Exception as e:
            self.display_error(f"Erreur: {e}")

    def search_contracts_command(self):
        """Rechercher des contrats"""
        try:
            current_user = self.auth_service.require_authentication()
            self.contract_controller.set_current_user(current_user)

            self.display_info("=== RECHERCHE DE CONTRATS ===")
            
            criteria = {}
            
            client_name = self.get_user_input("Nom du client (optionnel)")
            if client_name:
                criteria['client_name'] = client_name

            company_name = self.get_user_input("Nom de l'entreprise (optionnel)")
            if company_name:
                criteria['company_name'] = company_name

            status_display = {
                '1': 'Brouillon',
                '2': 'Signe',
                '3': 'Annule',
                '0': 'Tous'
            }
            
            status_choice = self.get_user_choice(status_display, "Statut")
            if status_choice != '0':
                status_options = {
                    '1': ContractStatus.DRAFT,
                    '2': ContractStatus.SIGNED,
                    '3': ContractStatus.CANCELLED,
                }
                criteria['status'] = status_options[status_choice]

            if not criteria:
                self.display_info("Aucun critere de recherche fourni")
                return

            contracts = self.contract_controller.search_contracts(**criteria)
            
            if contracts:
                self.display_success(f"{len(contracts)} contrat(s) trouve(s)")
                self._display_contracts_table(contracts)
            else:
                self.display_info("Aucun contrat correspondant trouve")

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(f"Erreur d'autorisation: {e}")
        except Exception as e:
            self.display_error(f"Erreur: {e}")

    def _display_contract_details(self, contract: Contract):
        """Afficher les details d'un contrat"""
        print(f"\n=== CONTRAT {contract.id} ===")
        print(f"Client: {contract.client.full_name}")
        print(f"Entreprise: {contract.client.company_name}")
        print(f"Commercial: {contract.commercial_contact.full_name}")
        print(f"Montant total: {contract.total_amount} EUR")
        print(f"Montant du: {contract.amount_due} EUR")
        print(f"Statut: {contract.status.value}")
        print(f"Signe: {'Oui' if contract.signed else 'Non'}")
        if contract.signed_at:
            print(f"Signe le: {contract.signed_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"Cree le: {contract.created_at.strftime('%Y-%m-%d %H:%M')}")
        if contract.updated_at:
            print(f"Modifie le: {contract.updated_at.strftime('%Y-%m-%d %H:%M')}")
        
        if contract.events:
            print(f"\nEvenements associes: {len(contract.events)}")
            for event in contract.events:
                support_name = (event.support_contact.full_name 
                               if event.support_contact else "Non assigne")
                print(f"  - {event.name} ({event.start_date.strftime('%Y-%m-%d')}) "
                      f"- Support: {support_name}")

    def _display_contracts_table(self, contracts: List[Contract]):
        """Afficher les contrats sous forme de tableau"""
        header = f"{'ID':<5} {'Client':<20} {'Entreprise':<20} {'Montant':<12} " \
                 f"{'Du':<12} {'Statut':<10} {'Commercial':<20}"
        print(header)
        print("-" * len(header))
        
        for contract in contracts:
            commercial_name = contract.commercial_contact.full_name[:19]
            status_display = contract.status.value
            print(f"{contract.id:<5} {contract.client.full_name[:19]:<20} "
                  f"{contract.client.company_name[:19]:<20} "
                  f"{contract.total_amount:<12} {contract.amount_due:<12} "
                  f"{status_display:<10} {commercial_name:<20}")