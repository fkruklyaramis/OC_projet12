from typing import List
from sqlalchemy.orm import sessionmaker
from src.database.connection import engine
from src.controllers.event_controller import EventController
from src.services.auth_service import AuthenticationService
from src.models.event import Event
from src.utils.auth_utils import AuthenticationError, AuthorizationError
from .base_view import BaseView


class EventView(BaseView):
    """Vue pour la gestion des événements - Pattern MVC"""

    def __init__(self):
        super().__init__()
        SessionLocal = sessionmaker(bind=engine)
        self.db = SessionLocal()
        self.event_controller = EventController(self.db)
        self.auth_service = AuthenticationService(self.db)
        
        current_user = self.auth_service.get_current_user()
        if current_user:
            self.event_controller.set_current_user(current_user)

    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()

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