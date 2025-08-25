from typing import Optional
from sqlalchemy.orm import sessionmaker
from src.database.connection import engine
from src.controllers.user_controller import UserController
from src.services.auth_service import AuthenticationService
from src.models.user import User, Department
from src.utils.auth_utils import AuthenticationError, AuthorizationError
from src.utils.validators import ValidationError
from .base_view import BaseView


class UserView(BaseView):
    """Vue pour la gestion des utilisateurs avec CRUD complet"""

    def __init__(self):
        super().__init__()
        SessionLocal = sessionmaker(bind=engine)
        self.db = SessionLocal()
        self.user_controller = UserController(self.db)
        self.auth_service = AuthenticationService(self.db)

        current_user = self.auth_service.get_current_user()
        if current_user:
            self.user_controller.set_current_user(current_user)

    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()

    def list_users_command(self, department: Optional[str] = None):
        """Lister les utilisateurs"""
        try:
            current_user = self.auth_service.require_authentication()
            self.user_controller.set_current_user(current_user)

            if department:
                users = self.user_controller.get_users_by_department(Department(department))
                self.display_header(f"UTILISATEURS - DÉPARTEMENT {department.upper()}")
            else:
                users = self.user_controller.get_all_users()
                self.display_header("TOUS LES UTILISATEURS")

            if not users:
                self.display_info("Aucun utilisateur trouvé")
                return

            self._display_users_table(users)

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(f"Erreur d'autorisation: {e}")
        except Exception as e:
            self.display_error(f"Erreur: {e}")

    def create_user_command(self):
        """Créer un nouveau collaborateur"""
        try:
            current_user = self.auth_service.require_authentication()
            self.user_controller.set_current_user(current_user)

            self.display_header("CRÉATION D'UN NOUVEAU COLLABORATEUR")

            # Collecter les informations
            employee_number = self.get_user_input("Numéro d'employé (format: EE000000)")
            email = self.get_user_input("Email")
            password = self.get_user_input("Mot de passe", password=True)
            full_name = self.get_user_input("Nom complet")

            departments = {
                '1': 'commercial',
                '2': 'support',
                '3': 'gestion'
            }
            department_choice = self.get_user_choice(departments, "Choisissez le département")

            user_data = {
                'employee_number': employee_number,
                'email': email,
                'password': password,
                'full_name': full_name,
                'department': departments[department_choice]
            }

            with self.console.status("[bold green]Création en cours..."):
                new_user = self.user_controller.create_user(user_data)

            success_content = f"""
[bold green]Collaborateur créé avec succès ![/bold green]

[cyan]ID:[/cyan] {new_user.id}
[cyan]Nom:[/cyan] {new_user.full_name}
[cyan]Email:[/cyan] {new_user.email}
[cyan]Département:[/cyan] {new_user.department.value.upper()}
[cyan]Numéro d'employé:[/cyan] {new_user.employee_number}
            """
            self.display_panel(success_content, "UTILISATEUR CRÉÉ", style="green")

        except ValidationError as e:
            self.display_error(f"Validation échouée: {e}")
        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(f"Erreur d'autorisation: {e}")
        except Exception as e:
            self.display_error(f"Erreur: {e}")

    def update_user_command(self, user_id: int):
        """Modifier un collaborateur"""
        try:
            current_user = self.auth_service.require_authentication()
            self.user_controller.set_current_user(current_user)

            # Récupérer l'utilisateur existant
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                self.display_error("Utilisateur non trouvé")
                return

            self.display_header(f"MODIFICATION DE {user.full_name}")

            # Afficher les informations actuelles
            self._display_user_details(user)

            self.console.print("\n[yellow]Laissez vide pour conserver la valeur actuelle[/yellow]")

            # Collecter les modifications
            update_data = {}

            new_email = self.get_user_input(f"Email ({user.email})")
            if new_email:
                update_data['email'] = new_email

            new_full_name = self.get_user_input(f"Nom complet ({user.full_name})")
            if new_full_name:
                update_data['full_name'] = new_full_name

            departments = {
                '1': 'commercial',
                '2': 'support',
                '3': 'gestion',
                '0': 'conserver'
            }
            dept_prompt = f"Département actuel: {user.department.value.upper()}"
            department_choice = self.get_user_choice(departments, dept_prompt)
            if department_choice != '0':
                update_data['department'] = departments[department_choice]

            if self.confirm_action("Changer le mot de passe ?"):
                new_password = self.get_user_input("Nouveau mot de passe", password=True)
                if new_password:
                    update_data['password'] = new_password

            if not update_data:
                self.display_info("Aucune modification apportée")
                return

            with self.console.status("[bold green]Mise à jour en cours..."):
                updated_user = self.user_controller.update_user(user_id, update_data)

            self.display_success("Utilisateur mis à jour avec succès")
            self._display_user_details(updated_user)

        except ValidationError as e:
            self.display_error(f"Validation échouée: {e}")
        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(f"Erreur d'autorisation: {e}")
        except Exception as e:
            self.display_error(f"Erreur: {e}")

    def delete_user_command(self, user_id: int):
        """Supprimer un collaborateur"""
        try:
            current_user = self.auth_service.require_authentication()
            self.user_controller.set_current_user(current_user)

            # Récupérer l'utilisateur
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                self.display_error("Utilisateur non trouvé")
                return

            self.display_header("SUPPRESSION D'UN COLLABORATEUR")
            self._display_user_details(user)

            if not self.confirm_action(
                f"Êtes-vous sûr de vouloir supprimer {user.full_name} ?"
            ):
                self.display_info("Suppression annulée")
                return

            with self.console.status("[bold red]Suppression en cours..."):
                success = self.user_controller.delete_user(user_id)

            if success:
                self.display_success("Utilisateur supprimé avec succès")
            else:
                self.display_error("Échec de la suppression")

        except ValidationError as e:
            self.display_error(f"Validation échouée: {e}")
        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(f"Erreur d'autorisation: {e}")
        except Exception as e:
            self.display_error(f"Erreur: {e}")

    def change_password_command(self, user_id: Optional[int] = None):
        """Changer un mot de passe"""
        try:
            current_user = self.auth_service.require_authentication()
            self.user_controller.set_current_user(current_user)

            # Si pas d'ID spécifié, utiliser l'utilisateur actuel
            if not user_id:
                user_id = current_user.id

            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                self.display_error("Utilisateur non trouvé")
                return

            self.display_header("CHANGEMENT DE MOT DE PASSE")

            if user_id == current_user.id:
                self.console.print("[cyan]Changement de votre mot de passe[/cyan]")
                old_password = self.get_user_input("Mot de passe actuel", password=True)
            else:
                self.console.print(f"[cyan]Changement du mot de passe de {user.full_name}[/cyan]")
                old_password = ""  # La gestion n'a pas besoin de l'ancien mot de passe

            new_password = self.get_user_input("Nouveau mot de passe", password=True)
            confirm_password = self.get_user_input("Confirmer le nouveau mot de passe", password=True)

            if new_password != confirm_password:
                self.display_error("Les mots de passe ne correspondent pas")
                return

            with self.console.status("[bold green]Changement en cours..."):
                success = self.user_controller.change_password(user_id, old_password, new_password)

            if success:
                self.display_success("Mot de passe changé avec succès")
            else:
                self.display_error("Échec du changement de mot de passe")

        except ValidationError as e:
            self.display_error(f"Validation échouée: {e}")
        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(f"Erreur d'autorisation: {e}")
        except Exception as e:
            self.display_error(f"Erreur: {e}")

    def search_users_command(self):
        """Rechercher des collaborateurs"""
        try:
            current_user = self.auth_service.require_authentication()
            self.user_controller.set_current_user(current_user)

            self.display_header("RECHERCHE DE COLLABORATEURS")

            criteria = {}

            email = self.get_user_input("Email (optionnel)")
            if email:
                criteria['email'] = email

            full_name = self.get_user_input("Nom (optionnel)")
            if full_name:
                criteria['full_name'] = full_name

            employee_number = self.get_user_input("Numéro d'employé (optionnel)")
            if employee_number:
                criteria['employee_number'] = employee_number

            departments = {
                '1': 'commercial',
                '2': 'support',
                '3': 'gestion',
                '0': 'tous'
            }
            dept_choice = self.get_user_choice(departments, "Département")
            if dept_choice != '0':
                criteria['department'] = Department(departments[dept_choice])

            if not criteria:
                self.display_info("Aucun critère de recherche fourni")
                return

            users = self.user_controller.search_users(**criteria)

            if users:
                self.display_success(f"{len(users)} collaborateur(s) trouvé(s)")
                self._display_users_table(users)
            else:
                self.display_info("Aucun collaborateur correspondant trouvé")

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(f"Erreur d'autorisation: {e}")
        except Exception as e:
            self.display_error(f"Erreur: {e}")

    def _display_users_table(self, users):
        """Afficher les utilisateurs sous forme de tableau"""
        columns = [
            {'name': 'ID', 'style': 'cyan', 'justify': 'right'},
            {'name': 'Nom', 'style': 'white'},
            {'name': 'Email', 'style': 'blue'},
            {'name': 'Département', 'style': 'green'},
            {'name': 'N° Employé', 'style': 'yellow'}
        ]

        data = []
        for user in users:
            data.append([
                str(user.id),
                user.full_name,
                user.email,
                user.department.value.upper(),
                user.employee_number
            ])

        self.display_table("Collaborateurs", columns, data)

    def _display_user_details(self, user: User):
        """Afficher les détails d'un utilisateur"""
        user_content = f"""
[cyan]ID:[/cyan] {user.id}
[cyan]Nom:[/cyan] {user.full_name}
[cyan]Email:[/cyan] {user.email}
[cyan]Département:[/cyan] {user.department.value.upper()}
[cyan]Numéro d'employé:[/cyan] {user.employee_number}
[cyan]Créé le:[/cyan] {user.created_at.strftime('%Y-%m-%d %H:%M')}
        """
        self.display_panel(user_content, "DÉTAILS DU COLLABORATEUR", style="blue")
