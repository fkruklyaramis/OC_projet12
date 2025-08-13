#!/usr/bin/env python
"""Interface en ligne de commande pour Epic Events CRM"""
import os
import sys
import getpass
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'epicevents.settings')

import django
django.setup()

from crm.jwt_auth import JWTAuthService
from crm.auth import PermissionService
from crm.data_service import DataService


def require_auth(func):
    """Decorateur pour exiger une authentification"""
    def wrapper(self, *args, **kwargs):
        if not JWTAuthService.is_authenticated():
            print("Cette commande necessite une authentification.")
            print("Utilisez 'python epicevents.py login' pour vous connecter.")
            return
        
        JWTAuthService.refresh_token_if_needed()
        return func(self, *args, **kwargs)
    return wrapper


class EpicEventsCLI:
    """Interface CLI pour Epic Events"""

    def __init__(self):
        self.commands = {
            'login': self.login,
            'logout': self.logout,
            'status': self.status,
            'whoami': self.whoami,
            'permissions': self.show_permissions,
            'debug': self.debug_token,
            'clear': self.clear_token,
            'clients': self.list_clients,
            'contracts': self.list_contracts,
            'events': self.list_events,
            'client': self.show_client,
            'contract': self.show_contract,
            'event': self.show_event,
            'help': self.show_help
        }

    def run(self, args):
        """Point d'entree principal"""
        if len(args) < 2:
            self.show_help()
            return

        command = args[1]
        if command in self.commands:
            self.commands[command](args[2:])
        else:
            print(f"Commande inconnue: {command}")
            self.show_help()

    def login(self, args):
        """Commande de connexion"""
        if len(args) > 0:
            username = args[0]
        else:
            username = input("Nom d'utilisateur: ")
        
        password = getpass.getpass("Mot de passe: ")
        
        token, message = JWTAuthService.login(username, password)
        print(message)
        
        if token:
            user, _ = JWTAuthService.get_current_user()
            if user:
                print(f"Utilisateur: {user.full_name}")
                print(f"Role: {user.get_role_display()}")
                print(f"Numero d'employe: {user.employee_number}")

    def logout(self, args):
        """Commande de deconnexion"""
        success, message = JWTAuthService.logout()
        print(message)

    def status(self, args):
        """Affiche le statut de la session"""
        token_info = JWTAuthService.get_token_info()
        
        if not token_info:
            print("Aucune session active")
            return
        
        print(f"Utilisateur connecte: {token_info['username']}")
        print(f"Role: {token_info['role']}")
        print(f"Numero d'employe: {token_info['employee_number']}")
        print(f"Expiration: {token_info['expires_at']}")
        
        if token_info['is_expired']:
            print("Session expiree")
        else:
            user, message = JWTAuthService.get_current_user()
            if user:
                print("Session active")
            else:
                print(f"Erreur: {message}")

    def whoami(self, args):
        """Affiche l'utilisateur actuel"""
        user, message = JWTAuthService.get_current_user()
        
        if user:
            print(f"Nom complet: {user.full_name}")
            print(f"Email: {user.email}")
            print(f"Role: {user.get_role_display()}")
            print(f"Numero d'employe: {user.employee_number}")
        else:
            print(f"Non connecte: {message}")

    def show_permissions(self, args):
        """Affiche les permissions de l'utilisateur actuel"""
        user, message = JWTAuthService.get_current_user()
        
        if not user:
            print(f"Non connecte: {message}")
            return
        
        permissions = PermissionService.get_user_permissions(user)
        print(f"Permissions pour {user.username} ({user.get_role_display()}):")
        for perm in permissions:
            print(f"  - {perm}")

    @require_auth
    def list_clients(self, args):
        """Liste tous les clients accessibles a l'utilisateur"""
        user, _ = JWTAuthService.get_current_user()
        if not user:
            return

        clients, message = DataService.get_all_clients(user)
        print(message)
        
        if clients:
            print("\nListe des clients:")
            print("-" * 80)
            for client in clients:
                print(f"ID: {client.id}")
                print(f"Entreprise: {client.company_name}")
                print(f"Contact: {client.first_name} {client.last_name}")
                print(f"Email: {client.email}")
                print(f"Commercial: {client.sales_contact.full_name}")
                print("-" * 40)

    @require_auth
    def list_contracts(self, args):
        """Liste tous les contrats accessibles a l'utilisateur"""
        user, _ = JWTAuthService.get_current_user()
        if not user:
            return

        contracts, message = DataService.get_all_contracts(user)
        print(message)
        
        if contracts:
            print("\nListe des contrats:")
            print("-" * 80)
            for contract in contracts:
                print(f"ID: {contract.id}")
                print(f"Client: {contract.client.company_name}")
                print(f"Commercial: {contract.sales_contact.full_name}")
                print(f"Montant total: {contract.total_amount}")
                print(f"Montant du: {contract.amount_due}")
                print(f"Signe: {'Oui' if contract.is_signed else 'Non'}")
                print("-" * 40)

    @require_auth
    def list_events(self, args):
        """Liste tous les evenements accessibles a l'utilisateur"""
        user, _ = JWTAuthService.get_current_user()
        if not user:
            return

        events, message = DataService.get_all_events(user)
        print(message)
        
        if events:
            print("\nListe des evenements:")
            print("-" * 80)
            for event in events:
                print(f"ID: {event.id}")
                print(f"Nom: {event.name}")
                print(f"Client: {event.contract.client.company_name}")
                print(f"Date debut: {event.event_date_start}")
                print(f"Lieu: {event.location}")
                print(f"Participants: {event.attendees}")
                support = event.support_contact.full_name if event.support_contact else "Non assigne"
                print(f"Support: {support}")
                print("-" * 40)

    @require_auth
    def show_client(self, args):
        """Affiche les details d'un client specifique"""
        if len(args) < 1:
            print("Usage: python epicevents.py client <id>")
            return

        user, _ = JWTAuthService.get_current_user()
        if not user:
            return

        try:
            client_id = int(args[0])
            client, message = DataService.get_client_by_id(user, client_id)
            
            if client:
                print(f"\nDetails du client {client_id}:")
                print("-" * 50)
                print(f"Entreprise: {client.company_name}")
                print(f"Contact: {client.first_name} {client.last_name}")
                print(f"Email: {client.email}")
                print(f"Telephone: {client.phone}")
                print(f"Mobile: {client.mobile}")
                print(f"Commercial: {client.sales_contact.full_name}")
                print(f"Cree le: {client.created_at}")
            else:
                print(f"Erreur: {message}")
                
        except ValueError:
            print("L'ID du client doit etre un nombre")

    @require_auth
    def show_contract(self, args):
        """Affiche les details d'un contrat specifique"""
        if len(args) < 1:
            print("Usage: python epicevents.py contract <id>")
            return

        user, _ = JWTAuthService.get_current_user()
        if not user:
            return

        try:
            contract_id = int(args[0])
            contract, message = DataService.get_contract_by_id(user, contract_id)
            
            if contract:
                print(f"\nDetails du contrat {contract_id}:")
                print("-" * 50)
                print(f"Client: {contract.client.company_name}")
                print(f"Commercial: {contract.sales_contact.full_name}")
                print(f"Montant total: {contract.total_amount}")
                print(f"Montant du: {contract.amount_due}")
                print(f"Signe: {'Oui' if contract.is_signed else 'Non'}")
                print(f"Cree le: {contract.created_at}")
            else:
                print(f"Erreur: {message}")
                
        except ValueError:
            print("L'ID du contrat doit etre un nombre")

    @require_auth
    def show_event(self, args):
        """Affiche les details d'un evenement specifique"""
        if len(args) < 1:
            print("Usage: python epicevents.py event <id>")
            return

        user, _ = JWTAuthService.get_current_user()
        if not user:
            return

        try:
            event_id = int(args[0])
            event, message = DataService.get_event_by_id(user, event_id)
            
            if event:
                print(f"\nDetails de l'evenement {event_id}:")
                print("-" * 50)
                print(f"Nom: {event.name}")
                print(f"Client: {event.contract.client.company_name}")
                print(f"Contrat: {event.contract.id}")
                print(f"Date debut: {event.event_date_start}")
                print(f"Date fin: {event.event_date_end}")
                print(f"Lieu: {event.location}")
                print(f"Participants: {event.attendees}")
                support = event.support_contact.full_name if event.support_contact else "Non assigne"
                print(f"Support: {support}")
                print(f"Notes: {event.notes}")
                print(f"Cree le: {event.created_at}")
            else:
                print(f"Erreur: {message}")
                
        except ValueError:
            print("L'ID de l'evenement doit etre un nombre")

    def debug_token(self, args):
        """Debug du token JWT"""
        result = JWTAuthService.debug_token()
        print(result)

    def clear_token(self, args):
        """Supprime le token corrompu"""
        JWTAuthService.logout()
        print("Token supprime")

    def show_help(self, args=None):
        """Affiche l'aide"""
        print("Epic Events CRM - Interface en ligne de commande")
        print()
        print("Commandes d'authentification:")
        print("  login [username]     - Se connecter")
        print("  logout              - Se deconnecter")
        print("  status              - Statut de la session")
        print("  whoami              - Informations utilisateur")
        print("  permissions         - Voir les permissions")
        print()
        print("Commandes de consultation (necessitent une authentification):")
        print("  clients             - Liste tous les clients")
        print("  contracts           - Liste tous les contrats")
        print("  events              - Liste tous les evenements")
        print("  client <id>         - Details d'un client")
        print("  contract <id>       - Details d'un contrat")
        print("  event <id>          - Details d'un evenement")
        print()
        print("Commandes utilitaires:")
        print("  debug               - Debug du token JWT")
        print("  clear               - Supprimer le token")
        print("  help                - Afficher cette aide")
        print()
        print("Exemples:")
        print("  python epicevents.py login john_doe")
        print("  python epicevents.py clients")
        print("  python epicevents.py client 1")
        print("  python epicevents.py logout")


if __name__ == '__main__':
    cli = EpicEventsCLI()
    cli.run(sys.argv)