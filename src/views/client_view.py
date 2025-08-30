from typing import Optional
from src.controllers.client_controller import ClientController
from src.models.client import Client
from src.models.user import User, Department
from src.utils.auth_utils import AuthenticationError, AuthorizationError
from src.utils.validators import ValidationError
from .base_view import BaseView


class ClientView(BaseView):
    """Vue pour la gestion des clients avec interface Rich"""

    def __init__(self):
        super().__init__()
        self.client_controller = self.setup_controller(ClientController)

    def create_client_command(self, commercial_id: Optional[int] = None):
        """Créer un nouveau client"""
        try:
            current_user = self.auth_service.require_authentication()
            self.client_controller.set_current_user(current_user)

            self.display_header("CRÉATION D'UN NOUVEAU CLIENT")

            # Collecter les informations du client
            full_name = self.get_user_input("Nom et prénom du client")
            email = self.get_user_input("Email")
            phone = self.get_user_input("Téléphone")
            company_name = self.get_user_input("Nom de l'entreprise")

            # Déterminer le commercial responsable
            if commercial_id:
                # Vérifier que le commercial existe
                commercial = self.db.query(User).filter(
                    User.id == commercial_id,
                    User.department == Department.COMMERCIAL
                ).first()
                if not commercial:
                    self.display_error(f"Commercial avec l'ID {commercial_id} non trouvé")
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
                        self.display_error("Aucun commercial disponible")
                        return

                    commercial_choices = {}
                    for i, commercial in enumerate(commercials, 1):
                        commercial_choices[str(i)] = f"{commercial.full_name} ({commercial.email})"

                    choice = self.get_user_choice(commercial_choices, "Choisissez le commercial responsable")
                    final_commercial_id = commercials[int(choice) - 1].id
                else:
                    self.display_error("Vous devez spécifier un commercial responsable")
                    return

            with self.console.status("[bold green]Création du client en cours..."):
                new_client = self.client_controller.create_client(
                    full_name=full_name,
                    email=email,
                    phone=phone,
                    company_name=company_name,
                    commercial_contact_id=final_commercial_id
                )

            success_content = f"""
[bold green]Client créé avec succès ![/bold green]

[cyan]ID:[/cyan] {new_client.id}
[cyan]Nom:[/cyan] {new_client.full_name}
[cyan]Email:[/cyan] {new_client.email}
[cyan]Téléphone:[/cyan] {new_client.phone}
[cyan]Entreprise:[/cyan] {new_client.company_name}
[cyan]Commercial:[/cyan] {new_client.commercial_contact.full_name}
            """
            self.display_panel(success_content, "CLIENT CRÉÉ", style="green")

        except ValidationError as e:
            self.display_error(f"Validation échouée: {e}")
        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(f"Erreur d'autorisation: {e}")
        except Exception as e:
            self.display_error(f"Erreur: {e}")

    def list_clients_command(self, my_clients: bool = False):
        """Lister les clients"""
        try:
            current_user = self.auth_service.require_authentication()
            self.client_controller.set_current_user(current_user)

            if my_clients:
                clients = self.client_controller.get_my_clients()
                self.display_header("MES CLIENTS")
            else:
                clients = self.client_controller.get_all_clients()
                self.display_header("TOUS LES CLIENTS")

            if not clients:
                self.display_info("Aucun client trouvé")
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
                self.display_error("Client non trouvé")
                return

            self.display_header(f"MODIFICATION DE {client.full_name}")

            # Afficher les informations actuelles
            self._display_client_details(client)

            self.console.print("\n[yellow]Laissez vide pour conserver la valeur actuelle[/yellow]")

            # Collecter les modifications
            update_data = {}

            new_full_name = self.get_user_input(f"Nom complet ({client.full_name})")
            if new_full_name:
                update_data['full_name'] = new_full_name

            new_email = self.get_user_input(f"Email ({client.email})")
            if new_email:
                update_data['email'] = new_email

            new_phone = self.get_user_input(f"Téléphone ({client.phone})")
            if new_phone:
                update_data['phone'] = new_phone

            new_company = self.get_user_input(f"Entreprise ({client.company_name})")
            if new_company:
                update_data['company_name'] = new_company

            # Changement de commercial (gestion uniquement)
            if current_user.is_gestion and self.confirm_action("Changer le commercial responsable ?"):
                commercials = self.db.query(User).filter(
                    User.department == Department.COMMERCIAL
                ).all()

                if commercials:
                    commercial_choices = {}
                    for i, commercial in enumerate(commercials, 1):
                        commercial_choices[str(i)] = f"{commercial.full_name} ({commercial.email})"

                    choice = self.get_user_choice(commercial_choices, "Nouveau commercial")
                    update_data['commercial_contact_id'] = commercials[int(choice) - 1].id

            if not update_data:
                self.display_info("Aucune modification apportée")
                return

            with self.console.status("[bold green]Mise à jour en cours..."):
                updated_client = self.client_controller.update_client(client_id, **update_data)

            self.display_success("Client mis à jour avec succès")
            self._display_client_details(updated_client)

        except ValidationError as e:
            self.display_error(f"Validation échouée: {e}")
        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(f"Erreur d'autorisation: {e}")
        except Exception as e:
            self.display_error(f"Erreur: {e}")

    def delete_client_command(self, client_id: int):
        """Supprimer un client (gestion uniquement)"""
        try:
            current_user = self.auth_service.require_authentication()
            self.client_controller.set_current_user(current_user)

            if not current_user.is_gestion:
                self.display_error("Seule la gestion peut supprimer des clients")
                return

            client = self.client_controller.get_client_by_id(client_id)
            if not client:
                self.display_error("Client non trouvé")
                return

            self.display_header("SUPPRESSION D'UN CLIENT")
            self._display_client_details(client)

            if not self.confirm_action(f"Êtes-vous sûr de vouloir supprimer {client.full_name} ?"):
                self.display_info("Suppression annulée")
                return

            # Vérifier les dépendances
            if hasattr(client, 'contracts') and client.contracts:
                self.display_error("Impossible de supprimer: ce client a des contrats actifs")
                return

            with self.console.status("[bold red]Suppression en cours..."):
                self.db.delete(client)
                self.db.commit()

            self.display_success("Client supprimé avec succès")

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(f"Erreur d'autorisation: {e}")
        except Exception as e:
            self.db.rollback()
            self.display_error(f"Erreur: {e}")

    def assign_client_command(self, client_id: int, commercial_id: int):
        """Assigner un client à un commercial (gestion uniquement)"""
        try:
            current_user = self.auth_service.require_authentication()
            self.client_controller.set_current_user(current_user)

            if not current_user.is_gestion:
                self.display_error("Seule la gestion peut réassigner des clients")
                return

            client = self.client_controller.get_client_by_id(client_id)
            if not client:
                self.display_error("Client non trouvé")
                return

            commercial = self.db.query(User).filter(
                User.id == commercial_id,
                User.department == Department.COMMERCIAL
            ).first()
            if not commercial:
                self.display_error("Commercial non trouvé")
                return

            with self.console.status("[bold green]Assignation en cours..."):
                updated_client = self.client_controller.update_client(
                    client_id, commercial_contact_id=commercial_id
                )

            success_content = f"""
[bold green]Client réassigné avec succès ![/bold green]

[cyan]Client:[/cyan] {updated_client.full_name}
[cyan]Nouveau commercial:[/cyan] {commercial.full_name} ({commercial.email})
            """
            self.display_panel(success_content, "RÉASSIGNATION RÉUSSIE", style="green")

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(f"Erreur d'autorisation: {e}")
        except Exception as e:
            self.display_error(f"Erreur: {e}")

    def search_clients_command(self):
        """Rechercher des clients par critères"""
        try:
            current_user = self.auth_service.require_authentication()
            self.client_controller.set_current_user(current_user)

            self.display_header("RECHERCHE DE CLIENTS")

            criteria = {}

            full_name = self.get_user_input("Nom (optionnel)")
            if full_name:
                criteria['full_name'] = full_name

            email = self.get_user_input("Email (optionnel)")
            if email:
                criteria['email'] = email

            company_name = self.get_user_input("Entreprise (optionnel)")
            if company_name:
                criteria['company_name'] = company_name

            if not criteria:
                self.display_info("Aucun critère de recherche fourni")
                return

            clients = self.client_controller.search_clients(**criteria)

            if clients:
                self.display_success(f"{len(clients)} client(s) trouvé(s)")
                self._display_clients_table(clients)
            else:
                self.display_info("Aucun client correspondant trouvé")

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(f"Erreur d'autorisation: {e}")
        except Exception as e:
            self.display_error(f"Erreur: {e}")

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
            data.append([
                str(client.id),
                client.full_name,
                client.email,
                client.company_name,
                client.commercial_contact.full_name if client.commercial_contact else "Non assigné"
            ])

        self.display_table("Clients", columns, data)

    def _display_client_details(self, client: Client):
        """Afficher les détails d'un client"""
        client_content = f"""
[cyan]ID:[/cyan] {client.id}
[cyan]Nom:[/cyan] {client.full_name}
[cyan]Email:[/cyan] {client.email}
[cyan]Téléphone:[/cyan] {client.phone}
[cyan]Entreprise:[/cyan] {client.company_name}
[cyan]Commercial:[/cyan] {client.commercial_contact.full_name if client.commercial_contact else "Non assigné"}
[cyan]Créé le:[/cyan] {client.created_at.strftime('%Y-%m-%d %H:%M')}
        """
        self.display_panel(client_content, "DÉTAILS DU CLIENT", style="blue")
