"""
Vue de gestion des clients pour Epic Events CRM

Ce module fournit l'interface utilisateur complète pour la gestion des clients
avec fonctionnalités CRUD, recherche avancée, affichage tabulaire et respect
des permissions par département.

Fonctionnalités principales:
    - Création de clients avec validation complète
    - Consultation et recherche de clients
    - Modification des informations clients
    - Affichage tabulaire avec Rich
    - Gestion des permissions par département

Interface utilisateur:
    - Formulaires interactifs pour saisie de données
    - Tables stylées pour affichage des résultats
    - Messages de feedback contextuels
    - Navigation intuitive avec prompts clairs
    - Validation en temps réel des entrées

Gestion des permissions:
    - COMMERCIAL: Accès à ses propres clients
    - GESTION: Administration complète des clients
    - SUPPORT: Lecture seule pour assistance technique
    - Validation automatique des droits d'accès

Architecture de données:
    - Intégration avec ClientController pour logique métier
    - Validation via DataValidator pour cohérence
    - Messages localisés pour feedback utilisateur
    - Gestion d'erreurs avec affichage approprié

Fichier: src/views/client_view.py
"""

from typing import Optional
from src.controllers.client_controller import ClientController
from src.models.client import Client
from src.models.user import User, Department
from src.utils.auth_utils import AuthenticationError, AuthorizationError
from src.utils.validators import ValidationError
from src.config.messages import (
    CLIENT_MESSAGES, PROMPTS, STATUS_MESSAGES,
    VALIDATION_MESSAGES, CONFIRMATIONS, GENERAL_MESSAGES
)
from .base_view import BaseView


class ClientView(BaseView):
    """
    Vue spécialisée pour la gestion des clients Epic Events.

    Cette classe fournit une interface utilisateur complète pour toutes
    les opérations liées aux clients, avec respect des permissions
    et validation des données.

    Responsabilités:
        - Interface de création/modification de clients
        - Affichage et recherche dans la base clients
        - Gestion des permissions par département
        - Validation des données saisies
        - Feedback utilisateur approprié selon contexte

    Permissions par département:
        - COMMERCIAL: CRUD sur ses propres clients
        - GESTION: Administration complète tous clients
        - SUPPORT: Lecture seule pour assistance

    Interface Rich:
        - Tables formatées pour listes de clients
        - Formulaires interactifs de saisie
        - Messages colorés selon gravité
        - Panels pour informations détaillées
    """

    def __init__(self):
        """
        Initialiser la vue clients avec contrôleur associé.

        Configure automatiquement le contrôleur client avec
        la session de base de données et les permissions utilisateur.
        """
        super().__init__()
        self.client_controller = self.setup_controller(ClientController)

    def create_client_command(self, commercial_id: Optional[int] = None):
        """
        Interface de création d'un nouveau client.

        Cette méthode gère le processus complet de création d'un client
        avec validation des données et gestion des permissions.

        Args:
            commercial_id: ID du commercial responsable (optionnel)

        Processus:
            1. Vérification authentification et permissions
            2. Collecte des informations client via prompts
            3. Détermination du commercial responsable
            4. Validation et création via contrôleur
            5. Feedback de confirmation ou d'erreur

        Validation:
            - Format email selon RFC standards
            - Numéro de téléphone français
            - Nom d'entreprise non vide
            - Permissions utilisateur pour création
        """
        try:
            current_user = self.auth_service.require_authentication()
            self.client_controller.set_current_user(current_user)

            self.display_header(CLIENT_MESSAGES["create_header"])

            # Collecter les informations du client
            full_name = self.get_user_input(PROMPTS["name"])
            email = self.get_user_input(PROMPTS["email"])
            phone = self.get_user_input(PROMPTS["phone"])
            company_name = self.get_user_input(PROMPTS["company"])

            # Déterminer le commercial responsable
            if commercial_id:
                # Vérifier que le commercial existe
                commercial = self.db.query(User).filter(
                    User.id == commercial_id,
                    User.department == Department.COMMERCIAL
                ).first()
                if not commercial:
                    self.display_error(CLIENT_MESSAGES["commercial_not_found"].format(commercial_id=commercial_id))
                    return
                final_commercial_id = commercial_id
            else:
                if current_user.is_commercial:
                    final_commercial_id = current_user.id
                elif current_user.is_gestion:
                    # Proposer une liste des commerciaux disponibles
                    commercials = self.db.query(User).filter(
                        User.department == Department.COMMERCIAL
                    ).all()

                    if not commercials:
                        self.display_error(CLIENT_MESSAGES["no_commercials_available"])
                        return

                    commercial_choices = {}
                    for i, commercial in enumerate(commercials, 1):
                        commercial_choices[str(i)] = f"{commercial.full_name} ({commercial.email})"

                    choice = self.get_user_choice(commercial_choices, PROMPTS["choose_commercial"])
                    final_commercial_id = commercials[int(choice) - 1].id
                else:
                    self.display_error(CLIENT_MESSAGES["commercial_required"])
                    return

            with self.console.status(STATUS_MESSAGES["creating_client"]):
                new_client = self.client_controller.create_client(
                    full_name=full_name,
                    email=email,
                    phone=phone,
                    company_name=company_name,
                    commercial_contact_id=final_commercial_id
                )

            success_content = f"""
{CLIENT_MESSAGES["create_success_content"]}

[cyan]ID:[/cyan] {new_client.id}
[cyan]Nom:[/cyan] {new_client.full_name}
[cyan]Email:[/cyan] {new_client.email}
[cyan]Téléphone:[/cyan] {new_client.phone}
[cyan]Entreprise:[/cyan] {new_client.company_name}
[cyan]Commercial:[/cyan] {new_client.commercial_contact.full_name}
            """
            self.display_panel(success_content, CLIENT_MESSAGES["client_created_title"], style="green")

        except ValidationError as e:
            self.display_error(VALIDATION_MESSAGES["validation_failed"].format(error=e))
        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(VALIDATION_MESSAGES["authorization_error"].format(error=e))
        except Exception as e:
            self.display_error(VALIDATION_MESSAGES["general_error"].format(error=e))

    def list_clients_command(self, my_clients: bool = False):
        """Lister les clients"""
        try:
            current_user = self.auth_service.require_authentication()
            self.client_controller.set_current_user(current_user)

            if my_clients:
                clients = self.client_controller.get_my_clients()
                self.display_header(CLIENT_MESSAGES["my_clients_header"])
            else:
                clients = self.client_controller.get_all_clients()
                self.display_header(CLIENT_MESSAGES["list_header"])

            if not clients:
                self.display_info(CLIENT_MESSAGES["no_clients_found"])
                return

            self._display_clients_table(clients)

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(VALIDATION_MESSAGES["authorization_error"].format(error=e))
        except Exception as e:
            self.display_error(VALIDATION_MESSAGES["general_error"].format(error=e))

    def update_client_command(self, client_id: int):
        """Modifier un client"""
        try:
            current_user = self.auth_service.require_authentication()
            self.client_controller.set_current_user(current_user)

            client = self.client_controller.get_client_by_id(client_id)
            if not client:
                self.display_error(CLIENT_MESSAGES["client_not_found"])
                return

            self.display_header(CLIENT_MESSAGES["update_form_header"].format(client_name=client.full_name))

            # Afficher les informations actuelles
            self._display_client_details(client)

            self.console.print(f"\n{GENERAL_MESSAGES['update_instructions']}")

            # Collecter les modifications
            update_data = {}

            new_full_name = self.get_user_input(PROMPTS["name_update"].format(current_value=client.full_name))
            if new_full_name:
                update_data['full_name'] = new_full_name

            new_email = self.get_user_input(PROMPTS["email_update"].format(current_value=client.email))
            if new_email:
                update_data['email'] = new_email

            new_phone = self.get_user_input(PROMPTS["phone_update"].format(current_value=client.phone))
            if new_phone:
                update_data['phone'] = new_phone

            new_company = self.get_user_input(PROMPTS["company_update"].format(current_value=client.company_name))
            if new_company:
                update_data['company_name'] = new_company

            # Changement de commercial (gestion uniquement)
            if current_user.is_gestion and self.confirm_action(CONFIRMATIONS["change_commercial"]):
                commercials = self.db.query(User).filter(
                    User.department == Department.COMMERCIAL
                ).all()

                if commercials:
                    commercial_choices = {}
                    for i, commercial in enumerate(commercials, 1):
                        commercial_choices[str(i)] = f"{commercial.full_name} ({commercial.email})"

                    choice = self.get_user_choice(commercial_choices, PROMPTS["new_commercial"])
                    update_data['commercial_contact_id'] = commercials[int(choice) - 1].id

            if not update_data:
                self.display_info(GENERAL_MESSAGES["no_changes_made"])
                return

            with self.console.status(STATUS_MESSAGES["updating_client"]):
                updated_client = self.client_controller.update_client(client_id, **update_data)

            self.display_success(CLIENT_MESSAGES["update_success"])
            self._display_client_details(updated_client)

        except ValidationError as e:
            self.display_error(VALIDATION_MESSAGES["validation_failed"].format(error=e))
        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(VALIDATION_MESSAGES["authorization_error"].format(error=e))
        except Exception as e:
            self.display_error(VALIDATION_MESSAGES["general_error"].format(error=e))

    def delete_client_command(self, client_id: int):
        """Supprimer un client (gestion uniquement)"""
        try:
            current_user = self.auth_service.require_authentication()
            self.client_controller.set_current_user(current_user)

            if not current_user.is_gestion:
                self.display_error(CLIENT_MESSAGES["permission_delete_only"])
                return

            client = self.client_controller.get_client_by_id(client_id)
            if not client:
                self.display_error(CLIENT_MESSAGES["client_not_found"])
                return

            self.display_header(CLIENT_MESSAGES["delete_header"])
            self._display_client_details(client)

            if not self.confirm_action(CONFIRMATIONS["delete_client_specific"].format(client_name=client.full_name)):
                self.display_info(GENERAL_MESSAGES["deletion_cancelled"])
                return

            # Vérifier les dépendances
            if hasattr(client, 'contracts') and client.contracts:
                self.display_error(CLIENT_MESSAGES["delete_with_contracts"])
                return

            with self.console.status(STATUS_MESSAGES["deleting_client"]):
                self.db.delete(client)
                self.db.commit()

            self.display_success(CLIENT_MESSAGES["delete_success"])

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(VALIDATION_MESSAGES["authorization_error"].format(error=e))
        except Exception as e:
            self.db.rollback()
            self.display_error(VALIDATION_MESSAGES["general_error"].format(error=e))

    def assign_client_command(self, client_id: int, commercial_id: int):
        """Assigner un client à un commercial (gestion uniquement)"""
        try:
            current_user = self.auth_service.require_authentication()
            self.client_controller.set_current_user(current_user)

            if not current_user.is_gestion:
                self.display_error(CLIENT_MESSAGES["permission_reassign_only"])
                return

            client = self.client_controller.get_client_by_id(client_id)
            if not client:
                self.display_error(CLIENT_MESSAGES["client_not_found"])
                return

            commercial = self.db.query(User).filter(
                User.id == commercial_id,
                User.department == Department.COMMERCIAL
            ).first()
            if not commercial:
                self.display_error(CLIENT_MESSAGES["commercial_not_found_simple"])
                return

            with self.console.status(STATUS_MESSAGES["assigning_client"]):
                updated_client = self.client_controller.update_client(
                    client_id, commercial_contact_id=commercial_id
                )

            success_content = f"""
{CLIENT_MESSAGES["reassignment_success_content"]}

[cyan]Client:[/cyan] {updated_client.full_name}
[cyan]Nouveau commercial:[/cyan] {commercial.full_name} ({commercial.email})
            """
            self.display_panel(success_content, CLIENT_MESSAGES["reassignment_success_title"], style="green")

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(VALIDATION_MESSAGES["authorization_error"].format(error=e))
        except Exception as e:
            self.display_error(VALIDATION_MESSAGES["general_error"].format(error=e))

    def search_clients_command(self):
        """Rechercher des clients par critères"""
        try:
            current_user = self.auth_service.require_authentication()
            self.client_controller.set_current_user(current_user)

            self.display_header(CLIENT_MESSAGES["search_header"])

            criteria = {}

            full_name = self.get_user_input(PROMPTS["name_optional"])
            if full_name:
                criteria['full_name'] = full_name

            email = self.get_user_input(PROMPTS["email_optional"])
            if email:
                criteria['email'] = email

            company_name = self.get_user_input(PROMPTS["company_optional"])
            if company_name:
                criteria['company_name'] = company_name

            if not criteria:
                self.display_info(GENERAL_MESSAGES["no_search_criteria"])
                return

            clients = self.client_controller.search_clients(**criteria)

            if clients:
                self.display_success(CLIENT_MESSAGES["search_results"].format(count=len(clients)))
                self._display_clients_table(clients)
            else:
                self.display_info(CLIENT_MESSAGES["no_search_results"])

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(VALIDATION_MESSAGES["authorization_error"].format(error=e))
        except Exception as e:
            self.display_error(VALIDATION_MESSAGES["general_error"].format(error=e))

    def _display_clients_table(self, clients):
        """Afficher les clients sous forme de tableau"""
        columns = [
            {'name': 'ID', 'style': 'cyan', 'justify': 'right'},
            {'name': 'Nom', 'style': 'white'},
            {'name': 'Email', 'style': 'blue'},
            {'name': 'Entreprise', 'style': 'green'},
            {'name': 'Commercial', 'style': 'yellow'}
        ]

        data = []
        for client in clients:
            commercial_name = (
                client.commercial_contact.full_name
                if client.commercial_contact
                else CLIENT_MESSAGES["no_commercial_assigned"]
            )
            data.append([
                str(client.id),
                client.full_name,
                client.email,
                client.company_name,
                commercial_name
            ])

        self.display_table("Clients", columns, data)

    def _display_client_details(self, client: Client):
        """Afficher les détails d'un client"""
        commercial_display = (
            client.commercial_contact.full_name
            if client.commercial_contact
            else CLIENT_MESSAGES["no_commercial_assigned"]
        )
        client_content = f"""
[cyan]ID:[/cyan] {client.id}
[cyan]Nom:[/cyan] {client.full_name}
[cyan]Email:[/cyan] {client.email}
[cyan]Téléphone:[/cyan] {client.phone}
[cyan]Entreprise:[/cyan] {client.company_name}
[cyan]Commercial:[/cyan] {commercial_display}
[cyan]Créé le:[/cyan] {client.created_at.strftime('%Y-%m-%d %H:%M')}
        """
        self.display_panel(client_content, CLIENT_MESSAGES["client_details_title"], style="blue")
