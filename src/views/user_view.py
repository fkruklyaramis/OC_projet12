from typing import Optional
from src.controllers.user_controller import UserController
from src.models.user import User
from src.utils.auth_utils import AuthenticationError, AuthorizationError
from src.utils.validators import ValidationError
from src.config.messages import USER_MESSAGES
from .base_view import BaseView


class UserView(BaseView):
    """Vue pour la gestion des utilisateurs avec interface Rich"""

    def __init__(self):
        super().__init__()
        self.user_controller = self.setup_controller(UserController)

    def create_user_command(self):
        """Créer un nouveau collaborateur (gestion uniquement)"""
        try:
            current_user = self.auth_service.require_authentication()
            self.user_controller.set_current_user(current_user)

            if not current_user.is_gestion:
                self.display_error("Seule la gestion peut créer des utilisateurs")
                return

            self.display_header("CRÉATION D'UN NOUVEAU COLLABORATEUR")

            # Collecter les informations utilisateur
            email = self.get_user_input("Email")
            full_name = self.get_user_input("Nom et prénom")
            password = self.get_user_input("Mot de passe", password=True)

            departments = {
                '1': 'commercial',
                '2': 'support',
                '3': 'gestion'
            }
            department_choice = self.get_user_choice(
                departments, "Choisissez le département"
            )

            with self.console.status("[bold green]Création en cours..."):
                new_user = self.user_controller.create_user(
                    email=email,
                    password=password,
                    full_name=full_name,
                    department=departments[department_choice]
                )

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

    def list_users_command(self, department: Optional[str] = None):
        """Lister les utilisateurs (gestion uniquement)"""
        try:
            current_user = self.auth_service.require_authentication()
            self.user_controller.set_current_user(current_user)

            if not current_user.is_gestion:
                self.display_error("Seule la gestion peut lister les utilisateurs")
                return

            if department:
                self.display_header(f"COLLABORATEURS - {department.upper()}")
            else:
                self.display_header(USER_MESSAGES["list_header"])

            users = self.user_controller.get_all_users(department)

            if not users:
                self.display_info(USER_MESSAGES["no_users_found"])
                return

            self._display_users_table(users)

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(f"Erreur d'autorisation: {e}")
        except Exception as e:
            self.display_error(f"Erreur: {e}")

    def update_user_command(self, user_id: int):
        """Modifier un collaborateur (gestion uniquement)"""
        try:
            current_user = self.auth_service.require_authentication()
            self.user_controller.set_current_user(current_user)

            if not current_user.is_gestion:
                self.display_error("Seule la gestion peut modifier des utilisateurs")
                return

            user = self.user_controller.get_user_by_id(user_id)
            if not user:
                self.display_error("Utilisateur non trouvé")
                return

            self.display_header(f"MODIFICATION DE {user.full_name}")
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

            if self.confirm_action("Changer le département ?"):
                departments = {
                    '1': 'commercial',
                    '2': 'support',
                    '3': 'gestion'
                }
                current_dept = user.department.value
                self.console.print(f"Département actuel: {current_dept}")
                department_choice = self.get_user_choice(
                    departments, "Nouveau département"
                )
                update_data['department'] = departments[department_choice]

            if self.confirm_action("Changer le mot de passe ?"):
                new_password = self.get_user_input("Nouveau mot de passe", password=True)
                update_data['password'] = new_password

            if not update_data:
                self.display_info("Aucune modification apportée")
                return

            with self.console.status("[bold green]Mise à jour en cours..."):
                updated_user = self.user_controller.update_user(user_id, **update_data)

            self.display_success(USER_MESSAGES["update_success"])
            self._display_user_details(updated_user)

        except ValidationError as e:
            self.display_error(f"Validation échouée: {e}")
        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(f"Erreur d'autorisation: {e}")
        except Exception as e:
            self.display_error(f"Erreur: {e}")

    def delete_user_command(self, user_id: int):
        """Supprimer un collaborateur (gestion uniquement)"""
        try:
            current_user = self.auth_service.require_authentication()
            self.user_controller.set_current_user(current_user)

            if not current_user.is_gestion:
                self.display_error("Seule la gestion peut supprimer des utilisateurs")
                return

            user = self.user_controller.get_user_by_id(user_id)
            if not user:
                self.display_error("Utilisateur non trouvé")
                return

            self.display_header("SUPPRESSION D'UN COLLABORATEUR")
            self._display_user_details(user)

            if not self.confirm_action(f"Êtes-vous sûr de vouloir supprimer {user.full_name} ?"):
                self.display_info("Suppression annulée")
                return

            with self.console.status("[bold red]Suppression en cours..."):
                success = self.user_controller.delete_user(user_id)

            if success:
                self.display_success("Utilisateur supprimé avec succès")

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(f"Erreur d'autorisation: {e}")
        except Exception as e:
            self.display_error(f"Erreur: {e}")

    def change_password_command(self, user_id: Optional[int] = None):
        """Changer le mot de passe"""
        try:
            current_user = self.auth_service.require_authentication()
            self.user_controller.set_current_user(current_user)

            # Si pas d'ID spécifié, changer son propre mot de passe
            if user_id is None:
                user_id = current_user.id
                target_user = current_user
                self.display_header("CHANGEMENT DE MON MOT DE PASSE")
            else:
                if not current_user.is_gestion:
                    self.display_error(
                        "Seule la gestion peut changer le mot de passe d'autres utilisateurs"
                    )
                    return

                target_user = self.user_controller.get_user_by_id(user_id)
                if not target_user:
                    self.display_error("Utilisateur non trouvé")
                    return

                self.display_header(f"CHANGEMENT DU MOT DE PASSE DE {target_user.full_name}")

            new_password = self.get_user_input("Nouveau mot de passe", password=True)
            confirm_password = self.get_user_input("Confirmer le mot de passe", password=True)

            if new_password != confirm_password:
                self.display_error("Les mots de passe ne correspondent pas")
                return

            with self.console.status("[bold green]Changement en cours..."):
                success = self.user_controller.change_password(user_id, new_password)

            if success:
                self.display_success("Mot de passe changé avec succès")

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(f"Erreur d'autorisation: {e}")
        except Exception as e:
            self.display_error(f"Erreur: {e}")

    def search_users_command(self):
        """Rechercher des collaborateurs (gestion uniquement)"""
        try:
            current_user = self.auth_service.require_authentication()
            self.user_controller.set_current_user(current_user)

            if not current_user.is_gestion:
                self.display_error("Seule la gestion peut rechercher des utilisateurs")
                return

            self.display_header("RECHERCHE DE COLLABORATEURS")

            criteria = {}

            full_name = self.get_user_input("Nom (optionnel)")
            if full_name:
                criteria['full_name'] = full_name

            email = self.get_user_input("Email (optionnel)")
            if email:
                criteria['email'] = email

            employee_number = self.get_user_input("Numéro d'employé (optionnel)")
            if employee_number:
                criteria['employee_number'] = employee_number

            department = self.get_user_input("Département (optionnel)")
            if department:
                criteria['department'] = department

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
        self.display_panel(user_content, "DÉTAILS DE L'UTILISATEUR", style="blue")
