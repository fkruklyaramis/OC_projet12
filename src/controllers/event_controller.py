from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from src.models.event import Event
from src.models.contract import Contract
from src.models.user import User, Department
from src.utils.auth_utils import AuthorizationError, PermissionChecker
from .base_controller import BaseController


class EventController(BaseController):
    """Controleur pour la gestion des evenements - Pattern MVC"""

    def __init__(self, db_session: Session):
        super().__init__(db_session)
        self.permission_checker = PermissionChecker()

    def get_all_events(self) -> List[Event]:
        """Recuperer tous les evenements avec verification des permissions"""
        if not self.permission_checker.has_permission(self.current_user, 'read_event'):
            raise AuthorizationError("Permission requise pour consulter les evenements")
        
        return self.db.query(Event).options(
            joinedload(Event.contract).joinedload(Contract.client),
            joinedload(Event.support_contact)
        ).all()

    def get_event_by_id(self, event_id: int) -> Optional[Event]:
        """Recuperer un evenement par son ID avec verification d'acces"""
        if not self.permission_checker.has_permission(self.current_user, 'read_event'):
            raise AuthorizationError("Permission requise pour consulter les evenements")
        
        event = self.db.query(Event).options(
            joinedload(Event.contract).joinedload(Contract.client),
            joinedload(Event.support_contact)
        ).filter(Event.id == event_id).first()
        
        if event and not self._can_access_event(event):
            raise AuthorizationError("Acces refuse a cet evenement")
        
        return event

    def get_my_events(self) -> List[Event]:
        """Recuperer les evenements assignes a l'utilisateur actuel"""
        if not self.current_user:
            raise AuthorizationError("Authentification requise")
        
        if self.current_user.is_support:
            return self.db.query(Event).options(
                joinedload(Event.contract).joinedload(Contract.client),
                joinedload(Event.support_contact)
            ).filter(Event.support_contact_id == self.current_user.id).all()
        
        elif self.current_user.is_commercial:
            # Commercial voit les evenements de ses contrats
            return self.db.query(Event).options(
                joinedload(Event.contract).joinedload(Contract.client),
                joinedload(Event.support_contact)
            ).join(Contract).filter(
                Contract.commercial_contact_id == self.current_user.id
            ).all()
        
        else:
            return self.get_all_events()

    def get_events_without_support(self) -> List[Event]:
        """Recuperer les evenements sans support assigne"""
        if not self.permission_checker.has_permission(self.current_user, 'read_event'):
            raise AuthorizationError("Permission requise pour consulter les evenements")
        
        return self.db.query(Event).options(
            joinedload(Event.contract).joinedload(Contract.client)
        ).filter(Event.support_contact_id.is_(None)).all()

    def get_upcoming_events(self, days_ahead: int = 30) -> List[Event]:
        """Recuperer les evenements a venir"""
        if not self.permission_checker.has_permission(self.current_user, 'read_event'):
            raise AuthorizationError("Permission requise pour consulter les evenements")
        
        from datetime import timedelta
        future_date = datetime.now() + timedelta(days=days_ahead)
        
        query = self.db.query(Event).options(
            joinedload(Event.contract).joinedload(Contract.client),
            joinedload(Event.support_contact)
        ).filter(
            Event.start_date >= datetime.now(),
            Event.start_date <= future_date
        )
        
        # Filtre pour les utilisateurs non-gestion
        if self.current_user.is_support:
            query = query.filter(Event.support_contact_id == self.current_user.id)
        elif self.current_user.is_commercial:
            query = query.join(Contract).filter(
                Contract.commercial_contact_id == self.current_user.id
            )
        
        return query.all()

    def search_events(self, **criteria) -> List[Event]:
        """Rechercher des evenements selon des criteres"""
        if not self.permission_checker.has_permission(self.current_user, 'read_event'):
            raise AuthorizationError("Permission requise pour consulter les evenements")
        
        query = self.db.query(Event).options(
            joinedload(Event.contract).joinedload(Contract.client),
            joinedload(Event.support_contact)
        )
        
        # Filtre par nom
        if 'name' in criteria and criteria['name']:
            query = query.filter(Event.name.ilike(f"%{criteria['name']}%"))
        
        # Filtre par lieu
        if 'location' in criteria and criteria['location']:
            query = query.filter(Event.location.ilike(f"%{criteria['location']}%"))
        
        # Filtre par date de debut
        if 'start_date' in criteria and criteria['start_date']:
            query = query.filter(Event.start_date >= criteria['start_date'])
        
        # Filtre par client
        if 'client_name' in criteria and criteria['client_name']:
            query = query.join(Contract).join(Client).filter(
                Client.full_name.ilike(f"%{criteria['client_name']}%")
            )
        
        # Filtres par permissions utilisateur
        if self.current_user.is_support:
            query = query.filter(Event.support_contact_id == self.current_user.id)
        elif self.current_user.is_commercial:
            query = query.join(Contract).filter(
                Contract.commercial_contact_id == self.current_user.id
            )
        
        return query.all()

    def create_event(self, contract_id: int, name: str, location: str, 
                    attendees: int, start_date: datetime, end_date: datetime,
                    notes: str = None) -> Event:
        """Creer un nouvel evenement"""
        if not self.permission_checker.has_permission(self.current_user, 'create_event'):
            raise AuthorizationError("Permission requise pour creer des evenements")
        
        # Verifier que le contrat existe et est signe
        contract = self.db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise ValueError("Contrat non trouve")
        
        if not contract.is_signed:
            raise ValueError("Le contrat doit etre signe pour creer un evenement")
        
        # Verifier les dates
        if end_date <= start_date:
            raise ValueError("La date de fin doit etre posterieure a la date de debut")
        
        try:
            event = Event(
                contract_id=contract_id,
                name=name,
                location=location,
                attendees=attendees,
                start_date=start_date,
                end_date=end_date,
                notes=notes
            )
            self.db.add(event)
            self.db.commit()
            self.db.refresh(event)
            return event
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erreur lors de la creation de l'evenement: {e}")

    def assign_support(self, event_id: int, support_user_id: int) -> Event:
        """Assigner un support a un evenement"""
        if not self.permission_checker.has_permission(self.current_user, 'update_event'):
            raise AuthorizationError("Permission requise pour assigner un support")
        
        event = self.get_event_by_id(event_id)
        if not event:
            raise ValueError("Evenement non trouve")
        
        # Verifier que l'utilisateur est du support
        support_user = self.db.query(User).filter(User.id == support_user_id).first()
        if not support_user or not support_user.is_support:
            raise ValueError("L'utilisateur doit appartenir au support")
        
        try:
            event.support_contact_id = support_user_id
            self.db.commit()
            self.db.refresh(event)
            return event
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erreur lors de l'assignation: {e}")

    def update_event(self, event_id: int, **kwargs) -> Event:
        """Modifier un evenement"""
        event = self.get_event_by_id(event_id)
        if not event:
            raise ValueError("Evenement non trouve")
        
        # Permissions speciales pour les modifications
        can_update = False
        if self.permission_checker.has_permission(self.current_user, 'update_event'):
            can_update = True
        elif (self.current_user.is_support and 
              self.permission_checker.has_permission(self.current_user, 'update_assigned_event') and
              event.support_contact_id == self.current_user.id):
            can_update = True
        
        if not can_update:
            raise AuthorizationError("Permission requise pour modifier cet evenement")
        
        try:
            forbidden_fields = ['id', 'contract_id', 'created_at']
            for key, value in kwargs.items():
                if key in forbidden_fields:
                    continue
                if hasattr(event, key):
                    setattr(event, key, value)
            
            self.db.commit()
            self.db.refresh(event)
            return event
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erreur lors de la modification: {e}")

    def _can_access_event(self, event: Event) -> bool:
        """Verifier si l'utilisateur peut acceder a cet evenement"""
        if self.current_user.is_gestion:
            return True
        
        if self.current_user.is_support:
            return event.support_contact_id == self.current_user.id
        
        if self.current_user.is_commercial:
            return event.contract.commercial_contact_id == self.current_user.id
        
        return False