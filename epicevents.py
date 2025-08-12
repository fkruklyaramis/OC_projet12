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
            'help': self.show_help
        }

    def run(self, args):
        """Point d'entrée principal"""
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
                print(f"Rôle: {user.get_role_display()}")
                print(f"Numéro d'employé: {user.employee_number}")

    def logout(self, args):
        """Commande de déconnexion"""
        success, message = JWTAuthService.logout()
        print(message)

    def status(self, args):
        """Affiche le statut de la session"""
        token_info = JWTAuthService.get_token_info()

        if not token_info:
            print("Aucune session active")
            return

        print(f"Utilisateur connecté: {token_info['username']}")
        print(f"Rôle: {token_info['role']}")
        print(f"Numéro d'employé: {token_info['employee_number']}")
        print(f"Expiration: {token_info['expires_at']}")

        if token_info['is_expired']:
            print("Session expirée")
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
            print(f"Rôle: {user.get_role_display()}")
            print(f"Numéro d'employé: {user.employee_number}")
        else:
            print(f"Non connecté: {message}")

    def show_permissions(self, args):
        """Affiche les permissions de l'utilisateur actuel"""
        user, message = JWTAuthService.get_current_user()

        if not user:
            print(f"Non connecté: {message}")
            return

        permissions = PermissionService.get_user_permissions(user)
        print(f"Permissions pour {user.username} ({user.get_role_display()}):")
        for perm in permissions:
            print(f"  - {perm}")

    def debug_token(self, args):
        """Debug du token JWT"""
        result = JWTAuthService.debug_token()
        print(result)

    def clear_token(self, args):
        """Supprime le token corrompu"""
        JWTAuthService.logout()
        print("Token supprimé")

    def show_help(self, args=None):
        """Affiche l'aide"""
        print("Epic Events CRM - Interface en ligne de commande")
        print()
        print("Commandes disponibles:")
        print("  login [username]     - Se connecter")
        print("  logout              - Se déconnecter")
        print("  status              - Statut de la session")
        print("  whoami              - Informations utilisateur")
        print("  permissions         - Voir les permissions")
        print("  debug               - Debug du token JWT")
        print("  clear               - Supprimer le token")
        print("  help                - Afficher cette aide")
        print()
        print("Exemples:")
        print("  python epicevents.py login john_doe")
        print("  python epicevents.py status")
        print("  python epicevents.py logout")


if __name__ == '__main__':
    cli = EpicEventsCLI()
    cli.run(sys.argv)
