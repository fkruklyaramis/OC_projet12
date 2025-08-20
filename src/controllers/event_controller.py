from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from src.models.event import Event
from src.models.contract import Contract
from src.models.client import Client
from src.models.user import User
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

        # Seule la gestion peut voir TOUS les evenements
        if not self.current_user.is_gestion:
            raise AuthorizationError("Seule la gestion peut consulter tous les evenements")

        return self.db.query(Event).options(
            joinedload(Event.contract).joinedload(Contract.client),
            joinedload(Event.contract).joinedload(Contract.commercial_contact),
            joinedload(Event.support_contact)
        ).all()

    def get_event_by_id(self, event_id: int) -> Optional[Event]:
        """Recuperer un evenement par son ID avec verification d'acces"""
        if not self.permission_checker.has_permission(self.current_user, 'read_event'):
            raise AuthorizationError("Permission requise pour consulter les evenements")

        event = self.db.query(Event).options(
            joinedload(Event.contract).joinedload(Contract.client),
            joinedload(Event.contract).joinedload(Contract.commercial_contact),
            joinedload(Event.support_contact)
        ).filter(Event.id == event_id).first()

        if event and not self._can_access_event(event):
            raise AuthorizationError("Acces refuse a cet evenement")

        return event

    def get_my_events(self) -> List[Event]:
        """Recuperer les evenements selon le role de l'utilisateur"""
        if not self.current_user:
            raise AuthorizationError("Authentification requise")

        query = self.db.query(Event).options(
            joinedload(Event.contract).joinedload(Contract.client),
            joinedload(Event.contract).joinedload(Contract.commercial_contact),
            joinedload(Event.support_contact)
        )

        if self.current_user.is_support:
            # Support voit uniquement les evenements qui lui sont assignes
            query = query.filter(Event.support_contact_id == self.current_user.id)
        elif self.current_user.is_commercial:
            # Commercial voit les evenements des contrats de ses clients
            query = query.join(Contract).filter(
                Contract.commercial_contact_id == self.current_user.id
            )
        elif self.current_user.is_gestion:
            # Gestion voit tous les evenements
            pass
        else:
            raise AuthorizationError("Role non autorise")

        return query.all()

    def get_upcoming_events(self, days_ahead: int = 30) -> List[Event]:
        """Recuperer les evenements a venir selon les permissions"""
        if not self.permission_checker.has_permission(self.current_user, 'read_event'):
            raise AuthorizationError("Permission requise pour consulter les evenements")

        end_date = datetime.now() + timedelta(days=days_ahead)

        query = self.db.query(Event).options(
            joinedload(Event.contract).joinedload(Contract.client),
            joinedload(Event.contract).joinedload(Contract.commercial_contact),
            joinedload(Event.support_contact)
        ).filter(
            Event.start_date >= datetime.now(),
            Event.start_date <= end_date
        )

        # Filtre par role utilisateur
        if self.current_user.is_support:
            query = query.filter(Event.support_contact_id == self.current_user.id)
        elif self.current_user.is_commercial:
            query = query.join(Contract).filter(
                Contract.commercial_contact_id == self.current_user.id
            )
        elif not self.current_user.is_gestion:
            raise AuthorizationError("Role non autorise")

        return query.order_by(Event.start_date).all()

    def get_events_without_support(self) -> List[Event]:
        """Recuperer les evenements sans support assigne"""
        if not self.permission_checker.has_permission(self.current_user, 'read_event'):
            raise AuthorizationError("Permission requise pour consulter les evenements")

        query = self.db.query(Event).options(
            joinedload(Event.contract).joinedload(Contract.client),
            joinedload(Event.contract).joinedload(Contract.commercial_contact)
        ).filter(Event.support_contact_id.is_(None))

        # Filtre par role utilisateur
        if self.current_user.is_commercial:
            query = query.join(Contract).filter(
                Contract.commercial_contact_id == self.current_user.id
            )
        elif self.current_user.is_support:
            # Support peut voir tous les evenements non assignes pour eventuellement s'y assigner
            pass
        elif not self.current_user.is_gestion:
            raise AuthorizationError("Role non autorise")

        return query.all()

    def search_events(self, **criteria) -> List[Event]:
        """Rechercher des evenements selon des criteres et permissions"""
        if not self.permission_checker.has_permission(self.current_user, 'read_event'):
            raise AuthorizationError("Permission requise pour consulter les evenements")

        query = self.db.query(Event).options(
            joinedload(Event.contract).joinedload(Contract.client),
            joinedload(Event.contract).joinedload(Contract.commercial_contact),
            joinedload(Event.support_contact)
        )

        # Filtres de recherche
        if 'name' in criteria and criteria['name']:
            query = query.filter(Event.name.ilike(f"%{criteria['name']}%"))

        if 'location' in criteria and criteria['location']:
            query = query.filter(Event.location.ilike(f"%{criteria['location']}%"))

        if 'client_name' in criteria and criteria['client_name']:
            query = query.join(Contract).join(Client).filter(
                Client.full_name.ilike(f"%{criteria['client_name']}%")
            )

        if 'start_date' in criteria and criteria['start_date']:
            query = query.filter(Event.start_date >= criteria['start_date'])

        # Filtre par role utilisateur
        if self.current_user.is_support:
            query = query.filter(Event.support_contact_id == self.current_user.id)
        elif self.current_user.is_commercial:
            query = query.join(Contract).filter(
                Contract.commercial_contact_id == self.current_user.id
            )
        elif not self.current_user.is_gestion:
            raise AuthorizationError("Role non autorise")

        return query.all()

    def create_event(self, contract_id: int, name: str, start_date: datetime,
                     end_date: datetime, location: str, attendees: int,
                     notes: str = None) -> Event:
        """Creer un nouvel evenement"""
        if not self.permission_checker.has_permission(self.current_user, 'create_event'):
            raise AuthorizationError("Permission requise pour creer des evenements")

        # Verifier que le contrat existe et est signe
        contract = self.db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise ValueError("Contrat non trouve")

        if not contract.signed:
            raise ValueError("Impossible de creer un evenement pour un contrat non signe")

        # Seul le commercial du contrat ou la gestion peut creer des evenements
        if (self.current_user.is_commercial and
            contract.commercial_contact_id != self.current_user.id and
                not self.current_user.is_gestion):
            raise AuthorizationError("Vous ne pouvez creer des evenements que pour vos contrats")

        try:
            event = Event(
                contract_id=contract_id,
                name=name,
                start_date=start_date,
                end_date=end_date,
                location=location,
                attendees=attendees,
                notes=notes
            )
            self.db.add(event)
            self.db.commit()
            self.db.refresh(event)
            return event
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erreur lors de la creation de l'evenement: {e}")

    def update_event(self, event_id: int, **kwargs) -> Event:
        """Modifier un evenement"""
        if not self.permission_checker.has_permission(self.current_user, 'update_event'):
            if not (self.current_user.is_support and
                    self.permission_checker.has_permission(self.current_user, 'update_assigned_event')):
                raise AuthorizationError("Permission requise pour modifier les evenements")

        event = self.get_event_by_id(event_id)
        if not event:
            raise ValueError("Evenement non trouve")

        if not self._can_access_event(event):
            raise AuthorizationError("Acces refuse a cet evenement")

        try:
            forbidden_fields = ['id', 'created_at', 'contract_id']

            # Support ne peut modifier que certains champs
            if self.current_user.is_support and not self.current_user.is_gestion:
                allowed_fields = ['notes', 'location', 'attendees']
                kwargs = {k: v for k, v in kwargs.items() if k in allowed_fields}

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

    def assign_support_to_event(self, event_id: int, support_user_id: int) -> Event:
        """Assigner un support a un evenement"""
        if not self.current_user.is_gestion:
            raise AuthorizationError("Seule la gestion peut assigner des supports")

        event = self.get_event_by_id(event_id)
        if not event:
            raise ValueError("Evenement non trouve")

        # Verifier que l'utilisateur est bien du support
        support_user = self.db.query(User).filter(User.id == support_user_id).first()
        if not support_user or not support_user.is_support:
            raise ValueError("L'utilisateur doit etre du departement SUPPORT")

        try:
            event.support_contact_id = support_user_id
            self.db.commit()
            self.db.refresh(event)
            return event
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erreur lors de l'assignation: {e}")

    def _can_access_event(self, event: Event) -> bool:
        """Verifier si l'utilisateur peut acceder a cet evenement"""
        if self.current_user.is_gestion:
            return True

        if self.current_user.is_support:
            return event.support_contact_id == self.current_user.id

        if self.current_user.is_commercial:
            return event.contract.commercial_contact_id == self.current_user.id

        return False
