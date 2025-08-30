from typing import List
from src.controllers.contract_controller import ContractController
from src.models.contract import Contract, ContractStatus
from src.utils.auth_utils import AuthenticationError, AuthorizationError
from src.config.messages import CONTRACT_MESSAGES, VALIDATION_MESSAGES
from .base_view import BaseView


class ContractView(BaseView):
    """Vue pour la gestion des contrats - Pattern MVC"""

    def __init__(self):
        super().__init__()
        self.contract_controller = self.setup_controller(ContractController)

    def list_all_contracts_command(self):
        """Lister tous les contrats (gestion seulement)"""
        try:
            current_user = self.auth_service.require_authentication()
            self.contract_controller.set_current_user(current_user)

            contracts = self.contract_controller.get_all_contracts()

            self.display_info(CONTRACT_MESSAGES["list_header"])

            if not contracts:
                self.display_info(CONTRACT_MESSAGES["no_contracts_found"])
                return

            self._display_contracts_table(contracts)

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(VALIDATION_MESSAGES["authorization_error"].format(error=e))
        except Exception as e:
            self.display_error(VALIDATION_MESSAGES["general_error"].format(error=e))

    def list_my_contracts_command(self):
        """Lister mes contrats (commerciaux seulement)"""
        try:
            current_user = self.auth_service.require_authentication()
            self.contract_controller.set_current_user(current_user)

            if not current_user.is_commercial:
                self.display_error(CONTRACT_MESSAGES["permission_commercial_only"])
                return

            contracts = self.contract_controller.get_my_contracts()

            self.display_info(CONTRACT_MESSAGES["my_contracts_header"])

            if not contracts:
                self.display_info(CONTRACT_MESSAGES["no_my_contracts"])
                return

            self._display_contracts_table(contracts)

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(VALIDATION_MESSAGES["authorization_error"].format(error=e))
        except Exception as e:
            self.display_error(VALIDATION_MESSAGES["general_error"].format(error=e))

    def list_unsigned_contracts_command(self):
        """Lister les contrats non signes selon les permissions"""
        try:
            current_user = self.auth_service.require_authentication()
            self.contract_controller.set_current_user(current_user)

            contracts = self.contract_controller.get_unsigned_contracts()

            role_info = ""
            if current_user.is_commercial:
                role_info = " (MES CONTRATS)"
            elif current_user.is_support:
                role_info = " (CONTRATS AVEC MES EVENEMENTS)"

            self.display_info(f"=== CONTRATS NON SIGNES{role_info} ===")

            if not contracts:
                self.display_info(CONTRACT_MESSAGES["no_unsigned_contracts"])
                return

            self._display_contracts_table(contracts)

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(VALIDATION_MESSAGES["authorization_error"].format(error=e))
        except Exception as e:
            self.display_error(VALIDATION_MESSAGES["general_error"].format(error=e))

    def list_unpaid_contracts_command(self):
        """Lister les contrats avec des montants dus selon les permissions"""
        try:
            current_user = self.auth_service.require_authentication()
            self.contract_controller.set_current_user(current_user)

            contracts = self.contract_controller.get_unpaid_contracts()

            role_info = ""
            if current_user.is_commercial:
                role_info = " (MES CONTRATS)"
            elif current_user.is_support:
                role_info = " (CONTRATS AVEC MES EVENEMENTS)"

            self.display_info(f"=== CONTRATS AVEC MONTANTS DUS{role_info} ===")

            if not contracts:
                self.display_info(CONTRACT_MESSAGES["no_pending_contracts"])
                return

            self._display_contracts_table(contracts)

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(VALIDATION_MESSAGES["authorization_error"].format(error=e))
        except Exception as e:
            self.display_error(VALIDATION_MESSAGES["general_error"].format(error=e))

    def view_contract_command(self, contract_id: int):
        """Afficher les details d'un contrat"""
        try:
            current_user = self.auth_service.require_authentication()
            self.contract_controller.set_current_user(current_user)

            contract = self.contract_controller.get_contract_by_id(contract_id)
            if not contract:
                self.display_error(CONTRACT_MESSAGES["not_found_or_access_denied"])
                return

            self._display_contract_details(contract)

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(VALIDATION_MESSAGES["authorization_error"].format(error=e))
        except Exception as e:
            self.display_error(VALIDATION_MESSAGES["general_error"].format(error=e))

    def search_contracts_command(self):
        """Rechercher des contrats selon les permissions"""
        try:
            current_user = self.auth_service.require_authentication()
            self.contract_controller.set_current_user(current_user)

            role_info = ""
            if current_user.is_commercial:
                role_info = " (DANS MES CONTRATS)"
            elif current_user.is_support:
                role_info = " (DANS MES EVENEMENTS)"

            self.display_info(f"=== RECHERCHE DE CONTRATS{role_info} ===")

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
                self.display_info(CONTRACT_MESSAGES["no_search_criteria"])
                return

            contracts = self.contract_controller.search_contracts(**criteria)

            if contracts:
                self.display_success(f"{len(contracts)} contrat(s) trouve(s)")
                self._display_contracts_table(contracts)
            else:
                self.display_info(CONTRACT_MESSAGES["no_search_results"])

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(VALIDATION_MESSAGES["authorization_error"].format(error=e))
        except Exception as e:
            self.display_error(VALIDATION_MESSAGES["general_error"].format(error=e))

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
                support_name = (event.support_contact.full_name[:14]
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

    def create_contract_command(self, client_id: int):
        """Créer un nouveau contrat pour un client"""
        from decimal import Decimal

        try:
            current_user = self.auth_service.require_authentication()
            self.contract_controller.set_current_user(current_user)

            # Vérifier que le client existe
            from src.controllers.client_controller import ClientController
            client_controller = ClientController(self.db)
            client_controller.set_current_user(current_user)

            client = client_controller.get_client_by_id(client_id)
            if not client:
                self.display_error(f"Client avec l'ID {client_id} introuvable")
                return

            self.display_info(f"\n────────────── CRÉATION D'UN CONTRAT POUR {client.full_name.upper()} ──────────────")

            # Saisie des données du contrat
            self.display_info(f"\nClient : {client.full_name}")
            self.display_info(f"Entreprise : {client.company_name}")
            self.display_info(f"Commercial : {client.commercial_contact.full_name}")

            print()

            # Montant total
            while True:
                try:
                    total_amount_input = self.prompt_user("Montant total du contrat (EUR)", required=True)
                    total_amount = Decimal(total_amount_input.replace(',', '.'))
                    if total_amount <= 0:
                        self.display_error("Le montant doit être positif")
                        continue
                    break
                except (ValueError, TypeError):
                    self.display_error("Montant invalide. Utilisez le format : 1000.50")

            # Montant restant dû
            while True:
                try:
                    amount_due_input = self.prompt_user("Montant restant dû (EUR)", required=True)
                    amount_due = Decimal(amount_due_input.replace(',', '.'))
                    if amount_due < 0:
                        self.display_error("Le montant dû ne peut pas être négatif")
                        continue
                    if amount_due > total_amount:
                        self.display_error("Le montant dû ne peut pas être supérieur au montant total")
                        continue
                    break
                except (ValueError, TypeError):
                    self.display_error("Montant invalide. Utilisez le format : 1000.50")

            # Statut du contrat
            print("\nChoisissez le statut du contrat :")
            print("  1 - draft (brouillon)")
            print("  2 - signed (signé)")
            print("  3 - cancelled (annulé)")

            while True:
                choice = self.prompt_user("Votre choix [1/2/3]", required=True)
                if choice == "1":
                    status = ContractStatus.DRAFT
                    break
                elif choice == "2":
                    status = ContractStatus.SIGNED
                    break
                elif choice == "3":
                    status = ContractStatus.CANCELLED
                    break
                else:
                    self.display_error("Choix invalide. Choisissez 1, 2 ou 3")

            # Créer le contrat
            contract = self.contract_controller.create_contract(
                client_id=client_id,
                total_amount=float(total_amount),
                amount_due=float(amount_due)
            )

            # Mettre à jour le statut si ce n'est pas DRAFT
            if status != ContractStatus.DRAFT:
                contract = self.contract_controller.update_contract(
                    contract_id=contract.id,
                    status=status
                )

            self.display_success_box(
                "CONTRAT CRÉÉ",
                f"Contrat créé avec succès !\n\n"
                f"ID: {contract.id}\n"
                f"Client: {contract.client.full_name}\n"
                f"Entreprise: {contract.client.company_name}\n"
                f"Montant total: {contract.total_amount} EUR\n"
                f"Montant dû: {contract.amount_due} EUR\n"
                f"Statut: {contract.status.value.upper()}\n"
                f"Commercial: {contract.commercial_contact.full_name}"
            )

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(VALIDATION_MESSAGES["authorization_error"].format(error=e))
        except Exception as e:
            self.display_error(f"Erreur lors de la création du contrat: {e}")

    def update_contract_command(self, contract_id: int):
        """Mettre à jour un contrat existant"""
        from decimal import Decimal

        try:
            current_user = self.auth_service.require_authentication()
            self.contract_controller.set_current_user(current_user)

            # Récupérer le contrat
            contract = self.contract_controller.get_contract_by_id(contract_id)
            if not contract:
                self.display_error(f"Contrat avec l'ID {contract_id} introuvable")
                return

            self.display_info(f"\n──────────────── MODIFICATION DU CONTRAT {contract.id} ────────────────")

            # Afficher les détails actuels
            self.display_info_box(
                "DÉTAILS DU CONTRAT",
                f"ID: {contract.id}\n"
                f"Client: {contract.client.full_name}\n"
                f"Entreprise: {contract.client.company_name}\n"
                f"Montant total: {contract.total_amount} EUR\n"
                f"Montant dû: {contract.amount_due} EUR\n"
                f"Statut: {contract.status.value.upper()}\n"
                f"Commercial: {contract.commercial_contact.full_name}\n"
                f"Créé le: {contract.created_at.strftime('%Y-%m-%d %H:%M')}"
            )

            print("\nLaissez vide pour conserver la valeur actuelle")

            # Montant total
            total_amount = None
            total_input = self.prompt_user(f"Montant total ({contract.total_amount} EUR)")
            if total_input.strip():
                try:
                    total_amount = float(Decimal(total_input.replace(',', '.')))
                    if total_amount <= 0:
                        self.display_error("Le montant doit être positif")
                        return
                except (ValueError, TypeError):
                    self.display_error("Montant invalide")
                    return

            # Montant restant dû
            amount_due = None
            due_input = self.prompt_user(f"Montant restant dû ({contract.amount_due} EUR)")
            if due_input.strip():
                try:
                    amount_due = float(Decimal(due_input.replace(',', '.')))
                    if amount_due < 0:
                        self.display_error("Le montant dû ne peut pas être négatif")
                        return
                    check_total = total_amount if total_amount is not None else contract.total_amount
                    if amount_due > check_total:
                        self.display_error("Le montant dû ne peut pas être supérieur au montant total")
                        return
                except (ValueError, TypeError):
                    self.display_error("Montant invalide")
                    return

            # Statut du contrat
            status = None
            change_status = self.prompt_user("Changer le statut ? [y/n]")
            if change_status.lower() in ['y', 'yes', 'o', 'oui']:
                print(f"\nStatut actuel: {contract.status.value}")
                print("\nNouveau statut :")
                print("  1 - draft (brouillon)")
                print("  2 - signed (signé)")
                print("  3 - cancelled (annulé)")

                while True:
                    choice = self.prompt_user("Votre choix [1/2/3]", required=True)
                    if choice == "1":
                        status = ContractStatus.DRAFT
                        break
                    elif choice == "2":
                        status = ContractStatus.SIGNED
                        break
                    elif choice == "3":
                        status = ContractStatus.CANCELLED
                        break
                    else:
                        self.display_error("Choix invalide. Choisissez 1, 2 ou 3")

            # Mettre à jour le contrat
            update_data = {}
            if total_amount is not None:
                update_data['total_amount'] = total_amount
            if amount_due is not None:
                update_data['amount_due'] = amount_due
            if status is not None:
                update_data['status'] = status

            updated_contract = self.contract_controller.update_contract(
                contract_id=contract_id,
                **update_data
            )

            self.display_success(CONTRACT_MESSAGES["update_success"])

            # Afficher les nouveaux détails
            self.display_info_box(
                "DÉTAILS DU CONTRAT",
                f"ID: {updated_contract.id}\n"
                f"Client: {updated_contract.client.full_name}\n"
                f"Entreprise: {updated_contract.client.company_name}\n"
                f"Montant total: {updated_contract.total_amount} EUR\n"
                f"Montant dû: {updated_contract.amount_due} EUR\n"
                f"Statut: {updated_contract.status.value.upper()}\n"
                f"Commercial: {updated_contract.commercial_contact.full_name}\n"
                f"Créé le: {updated_contract.created_at.strftime('%Y-%m-%d %H:%M')}"
            )

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(VALIDATION_MESSAGES["authorization_error"].format(error=e))
        except Exception as e:
            self.display_error(f"Erreur lors de la mise à jour du contrat: {e}")
