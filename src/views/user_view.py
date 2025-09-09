"""
Vue de gestion des utilisateurs pour Epic Events CRM

Ce module fournit l'interface d'administration des collaborateurs Epic Events
avec gestion des permissions, validation des données et interface Rich
pour les opérations CRUD réservées au département GESTION.

Fonctionnalités administratives:
    - Création de comptes collaborateurs
    - Consultation de l'annuaire interne
    - Modification des profils utilisateurs
    - Suppression de comptes (avec sécurité)
    - Recherche avancée dans l'équipe

Sécurité et permissions:
    - Accès réservé au département GESTION uniquement
    - Validation stricte des données utilisateur
    - Génération automatique de numéros d'employé
    - Politique de sécurité des mots de passe appliquée
    - Audit des modifications de comptes

Interface d'administration:
    - Formulaires de création/modification sécurisés
    - Affichage tabulaire des collaborateurs
    - Filtrage par département et statut
    - Confirmations pour actions critiques
    - Feedback détaillé sur opérations

Gestion des données RH:
    - Informations personnelles et professionnelles
    - Assignation départementale avec validation
    - Historique des modifications de comptes
    - Intégration avec système de permissions

Fichier: src/views/user_view.py
"""

from typing import Optional
from src.controllers.user_controller import UserController
from src.models.user import User
from src.utils.auth_utils import AuthenticationError, AuthorizationError
from src.utils.validators import ValidationError
from src.config.messages import USER_MESSAGES, STATUS_MESSAGES, VALIDATION_MESSAGES
from .base_view import BaseView


class UserView(BaseView):
    """
    Vue d'administration des utilisateurs Epic Events.

    Cette classe fournit une interface complète pour la gestion des comptes
    collaborateurs, réservée au département GESTION avec validation stricte
    des permissions et des données.

    Responsabilités administratives:
        - Création de comptes avec données complètes
        - Consultation et recherche dans l'annuaire
        - Modification sécurisée des profils
        - Suppression contrôlée de comptes
        - Gestion des permissions par département

    Sécurité RH:
        - Accès limité au département GESTION
        - Validation politique mots de passe
        - Génération sécurisée numéros employé
        - Audit des opérations sensibles
        - Protection données personnelles

    Interface administrative:
        - Formulaires structurés pour saisie complète
        - Tables formatées pour consultation rapide
        - Messages de confirmation pour actions critiques
        - Validation temps réel des entrées
        - Navigation intuitive dans l'annuaire
    """

    def __init__(self):
        """
        Initialiser la vue d'administration utilisateurs.

        Configure le contrôleur utilisateur avec session DB
        et permissions administratives requises.
        """
        super().__init__()
        self.user_controller = self.setup_controller(UserController)

    def create_user_command(self):
        """
        Interface de création d'un nouveau collaborateur.

        Cette méthode gère le processus complet de création d'un compte
        collaborateur avec validation des permissions GESTION et des données.

        Restrictions d'accès:
            - Réservé au département GESTION uniquement
            - Authentification requise avant opération
            - Validation automatique des permissions

        Processus de création:
            1. Vérification permissions administratives
            2. Collecte informations collaborateur via prompts
            3. Validation données selon politique entreprise
            4. Génération automatique numéro employé
            5. Création compte avec feedback confirmation

        Données collectées:
            - Email professionnel (unique et validé)
            - Nom complet (prénom + nom)
            - Numéro téléphone (format français)
            - Département d'affectation (enum validé)
            - Mot de passe sécurisé (politique appliquée)
        """
        try:
            current_user = self.auth_service.require_authentication()
            self.user_controller.set_current_user(current_user)

            if not current_user.is_gestion:
                self.display_error(USER_MESSAGES["permission_create_only"])
                return

            self.display_header(USER_MESSAGES["create_header"])

            # Collecter les informations utilisateur
            email = self.get_user_input(USER_MESSAGES["prompt_email"])
            full_name = self.get_user_input(USER_MESSAGES["prompt_full_name"])
            password = self.get_user_input(USER_MESSAGES["prompt_password"], password=True)

            departments = {
                '1': 'commercial',
                '2': 'support',
                '3': 'gestion'
            }
            department_choice = self.get_user_choice(
                departments, USER_MESSAGES["prompt_department"]
            )

            with self.console.status(STATUS_MESSAGES["creating_user"]):
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
            self.display_panel(success_content, USER_MESSAGES["title_user_created"], style="green")

        except ValidationError as e:
            self.display_error(VALIDATION_MESSAGES["validation_failed"].format(error=e))
        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(VALIDATION_MESSAGES["authorization_error"].format(error=e))
        except Exception as e:
            self.display_error(VALIDATION_MESSAGES["general_error"].format(error=e))

    def list_users_command(self, department: Optional[str] = None):
        """Lister les utilisateurs (gestion uniquement)"""
        try:
            current_user = self.auth_service.require_authentication()
            self.user_controller.set_current_user(current_user)

            if not current_user.is_gestion:
                self.display_error(USER_MESSAGES["permission_list_only"])
                return

            if department:
                self.display_header(USER_MESSAGES["list_header_department"].format(department=department.upper()))
            else:
                self.display_header(USER_MESSAGES["list_header"])

            users = self.user_controller.get_all_users(department)

            if not users:
                self.display_info(USER_MESSAGES["no_users_found"])
                return

            self._display_users_table(users)

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(VALIDATION_MESSAGES["authorization_error"].format(error=e))
        except Exception as e:
            self.display_error(VALIDATION_MESSAGES["general_error"].format(error=e))

    def update_user_command(self, user_id: int):
        """Modifier un collaborateur (gestion uniquement)"""
        try:
            current_user = self.auth_service.require_authentication()
            self.user_controller.set_current_user(current_user)

            if not current_user.is_gestion:
                self.display_error(USER_MESSAGES["permission_update_only"])
                return

            user = self.user_controller.get_user_by_id(user_id)
            if not user:
                self.display_error(USER_MESSAGES["user_not_found"])
                return

            self.display_header(USER_MESSAGES["update_header"].format(name=user.full_name))
            self._display_user_details(user)

            self.console.print(USER_MESSAGES["update_instruction"])

            # Collecter les modifications
            update_data = {}

            new_email = self.get_user_input(USER_MESSAGES["prompt_email_current"].format(current=user.email))
            if new_email:
                update_data['email'] = new_email

            new_full_name = self.get_user_input(
                USER_MESSAGES["prompt_full_name_current"].format(current=user.full_name)
            )
            if new_full_name:
                update_data['full_name'] = new_full_name

            if self.confirm_action(USER_MESSAGES["confirm_change_department"]):
                departments = {
                    '1': 'commercial',
                    '2': 'support',
                    '3': 'gestion'
                }
                current_dept = user.department.value
                self.console.print(USER_MESSAGES["current_department"].format(department=current_dept))
                department_choice = self.get_user_choice(
                    departments, USER_MESSAGES["prompt_new_department"]
                )
                update_data['department'] = departments[department_choice]

            if self.confirm_action(USER_MESSAGES["confirm_change_password"]):
                new_password = self.get_user_input(USER_MESSAGES["prompt_new_password"], password=True)
                update_data['password'] = new_password

            if not update_data:
                self.display_info(USER_MESSAGES["no_modifications"])
                return

            with self.console.status(STATUS_MESSAGES["updating_user"]):
                updated_user = self.user_controller.update_user(user_id, **update_data)

            self.display_success(USER_MESSAGES["update_success"])
            self._display_user_details(updated_user)

        except ValidationError as e:
            self.display_error(VALIDATION_MESSAGES["validation_failed"].format(error=e))
        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(VALIDATION_MESSAGES["authorization_error"].format(error=e))
        except Exception as e:
            self.display_error(VALIDATION_MESSAGES["general_error"].format(error=e))

    def delete_user_command(self, user_id: int):
        """Supprimer un collaborateur (gestion uniquement)"""
        try:
            current_user = self.auth_service.require_authentication()
            self.user_controller.set_current_user(current_user)

            if not current_user.is_gestion:
                self.display_error(USER_MESSAGES["permission_delete_only"])
                return

            user = self.user_controller.get_user_by_id(user_id)
            if not user:
                self.display_error(USER_MESSAGES["user_not_found"])
                return

            self.display_header(USER_MESSAGES["delete_header"])
            self._display_user_details(user)

            if not self.confirm_action(USER_MESSAGES["confirm_delete"].format(name=user.full_name)):
                self.display_info(USER_MESSAGES["delete_cancelled"])
                return

            with self.console.status(STATUS_MESSAGES["deleting_user"]):
                success = self.user_controller.delete_user(user_id)

            if success:
                self.display_success(USER_MESSAGES["delete_success"])

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(VALIDATION_MESSAGES["authorization_error"].format(error=e))
        except Exception as e:
            self.display_error(VALIDATION_MESSAGES["general_error"].format(error=e))

    def change_password_command(self, user_id: Optional[int] = None):
        """Changer le mot de passe"""
        try:
            current_user = self.auth_service.require_authentication()
            self.user_controller.set_current_user(current_user)

            # Si pas d'ID spécifié, changer son propre mot de passe
            if user_id is None:
                user_id = current_user.id
                target_user = current_user
                self.display_header(USER_MESSAGES["change_my_password_header"])
            else:
                if not current_user.is_gestion:
                    self.display_error(
                        USER_MESSAGES["permission_change_password_only"]
                    )
                    return

                target_user = self.user_controller.get_user_by_id(user_id)
                if not target_user:
                    self.display_error(USER_MESSAGES["user_not_found"])
                    return

                self.display_header(USER_MESSAGES["change_user_password_header"].format(name=target_user.full_name))

            new_password = self.get_user_input(USER_MESSAGES["prompt_new_password"], password=True)
            confirm_password = self.get_user_input(USER_MESSAGES["prompt_confirm_password"], password=True)

            if new_password != confirm_password:
                self.display_error(USER_MESSAGES["password_mismatch"])
                return

            with self.console.status(STATUS_MESSAGES["updating_user"]):
                success = self.user_controller.change_password(user_id, new_password)

            if success:
                self.display_success(USER_MESSAGES["password_change_success"])

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(VALIDATION_MESSAGES["authorization_error"].format(error=e))
        except Exception as e:
            self.display_error(VALIDATION_MESSAGES["general_error"].format(error=e))

    def search_users_command(self):
        """Rechercher des collaborateurs (gestion uniquement)"""
        try:
            current_user = self.auth_service.require_authentication()
            self.user_controller.set_current_user(current_user)

            if not current_user.is_gestion:
                self.display_error(USER_MESSAGES["permission_search_only"])
                return

            self.display_header(USER_MESSAGES["search_header"])

            criteria = {}

            full_name = self.get_user_input(USER_MESSAGES["prompt_search_name"])
            if full_name:
                criteria['full_name'] = full_name

            email = self.get_user_input(USER_MESSAGES["prompt_search_email"])
            if email:
                criteria['email'] = email

            employee_number = self.get_user_input(USER_MESSAGES["prompt_search_employee"])
            if employee_number:
                criteria['employee_number'] = employee_number

            department = self.get_user_input(USER_MESSAGES["prompt_search_department"])
            if department:
                criteria['department'] = department

            if not criteria:
                self.display_info(USER_MESSAGES["no_search_criteria"])
                return

            users = self.user_controller.search_users(**criteria)

            if users:
                self.display_success(USER_MESSAGES["search_results"].format(count=len(users)))
                self._display_users_table(users)
            else:
                self.display_info(USER_MESSAGES["no_search_results"])

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(VALIDATION_MESSAGES["authorization_error"].format(error=e))
        except Exception as e:
            self.display_error(VALIDATION_MESSAGES["general_error"].format(error=e))

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

        self.display_table(USER_MESSAGES["table_title"], columns, data)

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
        self.display_panel(user_content, USER_MESSAGES["title_user_details"], style="blue")
