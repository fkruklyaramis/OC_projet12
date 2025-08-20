import getpass
from sqlalchemy.orm import sessionmaker
from src.database.connection import engine
from src.services.auth_service import AuthenticationService
from src.utils.auth_utils import AuthenticationError, AuthorizationError
from .base_view import BaseView


class AuthView(BaseView):
    """Vue pour l'authentification - Pattern MVC"""

    def __init__(self):
        super().__init__()
        SessionLocal = sessionmaker(bind=engine)
        self.db = SessionLocal()
        self.auth_service = AuthenticationService(self.db)

    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()

    def login_command(self, email: str = None):
        """Commande de connexion"""
        try:
            if self.auth_service.is_authenticated():
                current_user = self.auth_service.get_current_user()
                if current_user:
                    self.display_info(f"Deja connecte en tant que: {current_user.full_name} "
                                     f"({current_user.email})")
                    
                    if not self.confirm_action("Voulez-vous vous reconnecter?"):
                        return
                    
                    self.auth_service.logout()

            if not email:
                email = self.get_user_input("Email")

            password = getpass.getpass("Mot de passe: ")

            user = self.auth_service.login(email, password)
            if user:
                self.display_success(f"Connexion reussie! Bienvenue {user.full_name}")
                self.display_info(f"Departement: {user.department.value}")
                self.display_info(f"Numero employe: {user.employee_number}")
            else:
                self.display_error("Echec de la connexion")

        except AuthenticationError as e:
            self.display_error(f"Erreur d'authentification: {e}")
        except Exception as e:
            self.display_error(f"Erreur: {e}")

    def logout_command(self):
        """Commande de deconnexion"""
        try:
            if not self.auth_service.is_authenticated():
                self.display_info("Vous n'etes pas connecte")
                return

            current_user = self.auth_service.get_current_user()
            if self.auth_service.logout():
                self.display_success(f"Deconnexion reussie. A bientot {current_user.full_name}!")
            else:
                self.display_error("Erreur lors de la deconnexion")

        except Exception as e:
            self.display_error(f"Erreur: {e}")

    def status_command(self):
        """Afficher le statut de connexion"""
        try:
            if self.auth_service.is_authenticated():
                user_data = self.auth_service.get_token_info()
                current_user = self.auth_service.get_current_user()
                
                if current_user and user_data:
                    print("=== STATUT DE CONNEXION ===")
                    print(f"Connecte: OUI")
                    print(f"Utilisateur: {current_user.full_name}")
                    print(f"Email: {current_user.email}")
                    print(f"Departement: {current_user.department.value}")
                    print(f"Numero employe: {current_user.employee_number}")
                    
                    from datetime import datetime, timezone
                    exp_timestamp = user_data.get('exp')
                    if exp_timestamp:
                        exp_date = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
                        remaining = exp_date - datetime.now(timezone.utc)
                        if remaining.total_seconds() > 0:
                            hours = int(remaining.total_seconds() // 3600)
                            minutes = int((remaining.total_seconds() % 3600) // 60)
                            print(f"Token expire dans: {hours}h {minutes}m")
                        else:
                            print("Token expire")
                else:
                    self.display_error("Token invalide ou expire")
            else:
                print("=== STATUT DE CONNEXION ===")
                print("Connecte: NON")
                print("Utilisez 'python epicevents.py login' pour vous connecter")

        except Exception as e:
            self.display_error(f"Erreur: {e}")

    def whoami_command(self):
        """Afficher l'utilisateur actuel"""
        try:
            current_user = self.auth_service.get_current_user()
            if current_user:
                print(f"{current_user.full_name} ({current_user.email})")
            else:
                print("Non connecte")
        except Exception as e:
            self.display_error(f"Erreur: {e}")