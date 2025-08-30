from typing import List
from src.controllers.event_controller import EventController
from src.models.event import Event
from src.utils.auth_utils import AuthenticationError, AuthorizationError
from .base_view import BaseView


class EventView(BaseView):
    """Vue pour la gestion des événements - Pattern MVC"""

    def __init__(self):
        super().__init__()
        self.event_controller = self.setup_controller(EventController)

    def list_all_events_command(self):
        """Lister tous les événements (gestion seulement)"""
        try:
            current_user = self.auth_service.require_authentication()
            self.event_controller.set_current_user(current_user)

            events = self.event_controller.get_all_events()

            self.display_info("=== TOUS LES EVENEMENTS ===")

            if not events:
                self.display_info("Aucun événement trouvé")
                return

            self._display_events_table(events)

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(f"Erreur d'autorisation: {e}")
        except Exception as e:
            self.display_error(f"Erreur: {e}")

    def list_my_events_command(self):
        """Lister mes événements selon le rôle"""
        try:
            current_user = self.auth_service.require_authentication()
            self.event_controller.set_current_user(current_user)

            events = self.event_controller.get_my_events()

            role_info = ""
            if current_user.is_support:
                role_info = " (ASSIGNES A MOI)"
            elif current_user.is_commercial:
                role_info = " (MES CONTRATS)"

            self.display_info(f"=== MES EVENEMENTS{role_info} ===")

            if not events:
                self.display_info("Aucun événement trouvé")
                return

            self._display_events_table(events)

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(f"Erreur d'autorisation: {e}")
        except Exception as e:
            self.display_error(f"Erreur: {e}")

    def list_upcoming_events_command(self, days_ahead: int = 30):
        """Lister les événements à venir"""
        try:
            current_user = self.auth_service.require_authentication()
            self.event_controller.set_current_user(current_user)

            events = self.event_controller.get_upcoming_events(days_ahead)

            role_info = ""
            if current_user.is_support:
                role_info = " (MES ASSIGNATIONS)"
            elif current_user.is_commercial:
                role_info = " (MES CONTRATS)"

            self.display_info(f"=== EVENEMENTS A VENIR ({days_ahead} JOURS){role_info} ===")

            if not events:
                self.display_info(f"Aucun événement dans les {days_ahead} prochains jours")
                return

            self._display_events_table(events)

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(f"Erreur d'autorisation: {e}")
        except Exception as e:
            self.display_error(f"Erreur: {e}")

    def list_unassigned_events_command(self):
        """Lister les événements sans support assigné"""
        try:
            current_user = self.auth_service.require_authentication()
            self.event_controller.set_current_user(current_user)

            events = self.event_controller.get_events_without_support()

            self.display_info("=== EVENEMENTS SANS SUPPORT ASSIGNE ===")

            if not events:
                self.display_info("Aucun événement sans support trouvé")
                return

            self._display_events_table(events)

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(f"Erreur d'autorisation: {e}")
        except Exception as e:
            self.display_error(f"Erreur: {e}")

    def view_event_command(self, event_id: int):
        """Afficher les détails d'un événement"""
        try:
            current_user = self.auth_service.require_authentication()
            self.event_controller.set_current_user(current_user)

            event = self.event_controller.get_event_by_id(event_id)
            if not event:
                self.display_error("Événement non trouvé ou accès refusé")
                return

            self._display_event_details(event)

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(f"Erreur d'autorisation: {e}")
        except Exception as e:
            self.display_error(f"Erreur: {e}")

    def search_events_command(self):
        """Rechercher des événements selon les permissions"""
        try:
            current_user = self.auth_service.require_authentication()
            self.event_controller.set_current_user(current_user)

            role_info = ""
            if current_user.is_support:
                role_info = " (MES ASSIGNATIONS)"
            elif current_user.is_commercial:
                role_info = " (MES CONTRATS)"

            self.display_info(f"=== RECHERCHE D'EVENEMENTS{role_info} ===")

            criteria = {}

            name = self.get_user_input("Nom de l'événement (optionnel)")
            if name:
                criteria['name'] = name

            location = self.get_user_input("Lieu (optionnel)")
            if location:
                criteria['location'] = location

            client_name = self.get_user_input("Nom du client (optionnel)")
            if client_name:
                criteria['client_name'] = client_name

            # Date de début
            start_date_str = self.get_user_input("Date de début (YYYY-MM-DD, optionnel)")
            if start_date_str:
                try:
                    from datetime import datetime
                    criteria['start_date'] = datetime.strptime(start_date_str, '%Y-%m-%d')
                except ValueError:
                    self.display_error("Format de date invalide. Utilisez YYYY-MM-DD")
                    return

            if not criteria:
                self.display_info("Aucun critère de recherche fourni")
                return

            events = self.event_controller.search_events(**criteria)

            if events:
                self.display_success(f"{len(events)} événement(s) trouvé(s)")
                self._display_events_table(events)
            else:
                self.display_info("Aucun événement correspondant trouvé")

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(f"Erreur d'autorisation: {e}")
        except Exception as e:
            self.display_error(f"Erreur: {e}")

    def _display_event_details(self, event: Event):
        """Afficher les détails d'un événement"""
        print(f"\n=== EVENEMENT {event.id} ===")
        print(f"Nom: {event.name}")
        print(f"Lieu: {event.location}")
        print(f"Participants: {event.attendees}")
        print(f"Date début: {event.start_date.strftime('%Y-%m-%d %H:%M')}")
        print(f"Date fin: {event.end_date.strftime('%Y-%m-%d %H:%M')}")
        print(f"Durée: {event.duration_days} jour(s)")

        if event.support_contact:
            print(f"Support assigné: {event.support_contact.full_name}")
        else:
            print("Support assigné: Non assigné")

        print(f"Contrat ID: {event.contract_id}")
        if event.contract:
            print(f"Client: {event.contract.client.full_name}")
            print(f"Entreprise: {event.contract.client.company_name}")
            print(f"Commercial: {event.contract.commercial_contact.full_name}")

        if event.notes:
            print(f"Notes: {event.notes}")

        print(f"Créé le: {event.created_at.strftime('%Y-%m-%d %H:%M')}")
        if event.updated_at:
            print(f"Modifié le: {event.updated_at.strftime('%Y-%m-%d %H:%M')}")

    def _display_events_table(self, events: List[Event]):
        """Afficher les événements sous forme de tableau"""
        header = f"{'ID':<5} {'Nom':<25} {'Client':<20} {'Date':<12} " \
                 f"{'Lieu':<20} {'Support':<15}"
        print(header)
        print("-" * len(header))

        for event in events:
            client_name = event.contract.client.full_name[:19] if event.contract else "N/A"
            support_name = (event.support_contact.full_name[:14]
                            if event.support_contact else "Non assigné")
            date_str = event.start_date.strftime('%Y-%m-%d')

            print(f"{event.id:<5} {event.name[:24]:<25} {client_name:<20} "
                  f"{date_str:<12} {event.location[:19]:<20} {support_name:<15}")

    def _get_available_supports(self):
        """Récupérer la liste des utilisateurs support disponibles"""
        from src.models.user import User, Department
        supports = self.db.query(User).filter(User.department == Department.SUPPORT).all()
        return supports

    def _prompt_support_selection(self, current_support_id=None):
        """Interface pour sélectionner un support"""
        supports = self._get_available_supports()

        if not supports:
            self.display_warning("Aucun utilisateur support disponible")
            return None

        print("\nSupport assigné :")
        print("  0 - Aucun support (non assigné)")

        for i, support in enumerate(supports, 1):
            current_marker = " (actuel)" if current_support_id == support.id else ""
            print(f"  {i} - {support.full_name} ({support.email}){current_marker}")

        while True:
            try:
                choice = self.prompt_user(f"Votre choix [0-{len(supports)}]", required=True)
                choice_int = int(choice)

                if choice_int == 0:
                    return None
                elif 1 <= choice_int <= len(supports):
                    return supports[choice_int - 1].id
                else:
                    self.display_error(f"Choix invalide. Choisissez entre 0 et {len(supports)}")
            except ValueError:
                self.display_error("Veuillez saisir un nombre valide")

    def create_event_command(self, contract_id: int):
        """Créer un nouvel événement pour un contrat"""
        from datetime import datetime

        try:
            current_user = self.auth_service.require_authentication()
            self.event_controller.set_current_user(current_user)

            # Vérifier que le contrat existe et est signé
            from src.controllers.contract_controller import ContractController
            contract_controller = ContractController(self.db)
            contract_controller.set_current_user(current_user)

            contract = contract_controller.get_contract_by_id(contract_id)
            if not contract:
                self.display_error(f"Contrat avec l'ID {contract_id} introuvable")
                return

            from src.models.contract import ContractStatus
            if contract.status != ContractStatus.SIGNED:
                self.display_error("Seuls les contrats signés peuvent avoir des événements")
                return

            self.display_info(f"\n─────────── CRÉATION D'UN ÉVÉNEMENT POUR LE CONTRAT {contract.id} ───────────")

            # Afficher les détails du contrat
            self.display_info(f"\nContrat : #{contract.id}")
            self.display_info(f"Client : {contract.client.full_name}")
            self.display_info(f"Entreprise : {contract.client.company_name}")
            self.display_info(f"Commercial : {contract.commercial_contact.full_name}")

            print()

            # Saisie des données de l'événement
            name = self.prompt_user("Nom de l'événement", required=True)

            # Date et heure de début
            while True:
                try:
                    start_date_str = self.prompt_user("Date de début (YYYY-MM-DD HH:MM)", required=True)
                    start_date = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M")

                    if start_date < datetime.now():
                        self.display_error("La date de début ne peut pas être dans le passé")
                        continue
                    break
                except ValueError:
                    self.display_error("Format de date invalide. Utilisez : YYYY-MM-DD HH:MM")

            # Date et heure de fin
            while True:
                try:
                    end_date_str = self.prompt_user("Date de fin (YYYY-MM-DD HH:MM)", required=True)
                    end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M")

                    if end_date <= start_date:
                        self.display_error("La date de fin doit être après la date de début")
                        continue
                    break
                except ValueError:
                    self.display_error("Format de date invalide. Utilisez : YYYY-MM-DD HH:MM")

            # Lieu
            location = self.prompt_user("Lieu de l'événement", required=True)

            # Nombre d'invités
            while True:
                try:
                    attendees_str = self.prompt_user("Nombre d'invités", required=True)
                    attendees = int(attendees_str)
                    if attendees < 0:
                        self.display_error("Le nombre d'invités doit être positif")
                        continue
                    break
                except ValueError:
                    self.display_error("Veuillez saisir un nombre valide")

            # Notes (optionnel)
            notes = self.prompt_user("Notes sur l'événement (optionnel)")
            if not notes.strip():
                notes = None

            # Sélection du support (optionnel)
            support_contact_id = self._prompt_support_selection()

            # Créer l'événement
            event = self.event_controller.create_event(
                contract_id=contract_id,
                name=name,
                start_date=start_date,
                end_date=end_date,
                location=location,
                attendees=attendees,
                notes=notes,
                support_contact_id=support_contact_id
            )

            self.display_success_box(
                "ÉVÉNEMENT CRÉÉ",
                f"Événement créé avec succès !\n\n"
                f"ID: {event.id}\n"
                f"Nom: {event.name}\n"
                f"Contrat: #{event.contract.id}\n"
                f"Client: {event.contract.client.full_name}\n"
                f"Date de début: {event.start_date.strftime('%Y-%m-%d %H:%M')}\n"
                f"Date de fin: {event.end_date.strftime('%Y-%m-%d %H:%M')}\n"
                f"Lieu: {event.location}\n"
                f"Invités: {event.attendees}\n"
                f"Support assigné: {'Non assigné' if not event.support_contact else event.support_contact.full_name}"
            )

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(f"Erreur d'autorisation: {e}")
        except Exception as e:
            self.display_error(f"Erreur lors de la création de l'événement: {e}")

    def update_event_command(self, event_id: int):
        """Mettre à jour un événement existant"""
        from datetime import datetime

        try:
            current_user = self.auth_service.require_authentication()
            self.event_controller.set_current_user(current_user)

            # Récupérer l'événement
            event = self.event_controller.get_event_by_id(event_id)
            if not event:
                self.display_error(f"Événement avec l'ID {event_id} introuvable")
                return

            self.display_info(f"\n────────────── MODIFICATION DE L'ÉVÉNEMENT {event.id} ──────────────")

            # Afficher les détails actuels
            self.display_info_box(
                "DÉTAILS DE L'ÉVÉNEMENT",
                f"ID: {event.id}\n"
                f"Nom: {event.name}\n"
                f"Contrat: #{event.contract.id}\n"
                f"Client: {event.contract.client.full_name}\n"
                f"Date de début: {event.start_date.strftime('%Y-%m-%d %H:%M')}\n"
                f"Date de fin: {event.end_date.strftime('%Y-%m-%d %H:%M')}\n"
                f"Lieu: {event.location}\n"
                f"Invités: {event.attendees}\n"
                f"Support: {'Non assigné' if not event.support_contact else event.support_contact.full_name}\n"
                f"Créé le: {event.created_at.strftime('%Y-%m-%d %H:%M')}"
            )

            print("\nLaissez vide pour conserver la valeur actuelle")

            # Nom de l'événement
            name = self.prompt_user(f"Nom ({event.name})")
            if not name.strip():
                name = None

            # Date de début
            start_date = None
            start_input = self.prompt_user(f"Date de début ({event.start_date.strftime('%Y-%m-%d %H:%M')})")
            if start_input.strip():
                try:
                    start_date = datetime.strptime(start_input, "%Y-%m-%d %H:%M")
                    if start_date < datetime.now():
                        self.display_error("La date de début ne peut pas être dans le passé")
                        return
                except ValueError:
                    self.display_error("Format de date invalide")
                    return

            # Date de fin
            end_date = None
            end_input = self.prompt_user(f"Date de fin ({event.end_date.strftime('%Y-%m-%d %H:%M')})")
            if end_input.strip():
                try:
                    end_date = datetime.strptime(end_input, "%Y-%m-%d %H:%M")
                    check_start = start_date if start_date is not None else event.start_date
                    if end_date <= check_start:
                        self.display_error("La date de fin doit être après la date de début")
                        return
                except ValueError:
                    self.display_error("Format de date invalide")
                    return

            # Lieu
            location = self.prompt_user(f"Lieu ({event.location})")
            if not location.strip():
                location = None

            # Nombre d'invités
            attendees = None
            attendees_input = self.prompt_user(f"Nombre d'invités ({event.attendees})")
            if attendees_input.strip():
                try:
                    attendees = int(attendees_input)
                    if attendees < 0:
                        self.display_error("Le nombre d'invités doit être positif")
                        return
                except ValueError:
                    self.display_error("Nombre invalide")
                    return

            # Notes
            notes = self.prompt_user(f"Notes ({event.notes or 'Aucune'})")
            if not notes.strip():
                notes = None

            # Support assigné
            support_contact_id = None
            change_support = self.prompt_user("Changer le support assigné ? [y/n]")
            if change_support.lower() in ['y', 'yes', 'o', 'oui']:
                current_support_id = event.support_contact_id
                support_contact_id = self._prompt_support_selection(current_support_id)

            # Mettre à jour l'événement
            update_data = {}
            if name is not None:
                update_data['name'] = name
            if start_date is not None:
                update_data['start_date'] = start_date
            if end_date is not None:
                update_data['end_date'] = end_date
            if location is not None:
                update_data['location'] = location
            if attendees is not None:
                update_data['attendees'] = attendees
            if notes is not None:
                update_data['notes'] = notes
            if support_contact_id is not None or change_support.lower() in ['y', 'yes', 'o', 'oui']:
                update_data['support_contact_id'] = support_contact_id

            updated_event = self.event_controller.update_event(
                event_id=event_id,
                **update_data
            )

            self.display_success("✓ Événement mis à jour avec succès")

            support_display = ("Non assigné" if not updated_event.support_contact
                               else updated_event.support_contact.full_name)

            # Afficher les nouveaux détails
            self.display_info_box(
                "DÉTAILS DE L'ÉVÉNEMENT",
                f"ID: {updated_event.id}\n"
                f"Nom: {updated_event.name}\n"
                f"Contrat: #{updated_event.contract.id}\n"
                f"Client: {updated_event.contract.client.full_name}\n"
                f"Date de début: {updated_event.start_date.strftime('%Y-%m-%d %H:%M')}\n"
                f"Date de fin: {updated_event.end_date.strftime('%Y-%m-%d %H:%M')}\n"
                f"Lieu: {updated_event.location}\n"
                f"Invités: {updated_event.attendees}\n"
                f"Support: {support_display}\n"
                f"Créé le: {updated_event.created_at.strftime('%Y-%m-%d %H:%M')}"
            )

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(f"Erreur d'autorisation: {e}")
        except Exception as e:
            self.display_error(f"Erreur lors de la mise à jour de l'événement: {e}")

    def assign_support_command(self, event_id: int, support_id: int):
        """Assigner un support à un événement"""
        try:
            current_user = self.auth_service.require_authentication()
            self.event_controller.set_current_user(current_user)

            updated_event = self.event_controller.assign_support_to_event(event_id, support_id)

            self.display_success_box(
                "SUPPORT ASSIGNÉ",
                f"Support assigné avec succès !\n\n"
                f"Événement: {updated_event.name}\n"
                f"Support: {updated_event.support_contact.full_name}\n"
                f"Client: {updated_event.contract.client.full_name}"
            )

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(f"Erreur d'autorisation: {e}")
        except Exception as e:
            self.display_error(f"Erreur lors de l'assignation: {e}")
