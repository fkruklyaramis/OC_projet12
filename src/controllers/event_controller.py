from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from src.models.event import Event
from src.models.contract import Contract, ContractStatus
from src.models.client import Client
from src.models.user import User
from src.utils.auth_utils import AuthorizationError, PermissionChecker
from src.utils.validators import DataValidator, ValidationError
from .base_controller import BaseController


class EventController(BaseController):
    """Controleur pour la gestion des evenements - Pattern MVC"""

    def __init__(self, db_session: Session):
        super().__init__(db_session)
        self.permission_checker = PermissionChecker()
        self.validator = DataValidator()

    def create_event(self, contract_id: int, name: str, start_date: datetime,
                     end_date: datetime, location: str, attendees: int,
                     notes: str = None) -> Event:
        """Creer un nouvel evenement"""
        if not self.permission_checker.has_permission(self.current_user, 'create_event'):
            raise AuthorizationError("Permission requise pour créer des événements")

        try:
            # Validation des données
            validated_name = self.validator.validate_event_name(name)
            validated_location = self.validator.validate_location(location)
            validated_attendees = self.validator.validate_attendees_count(attendees)
            self.validator.validate_date_range(start_date, end_date)

            # Vérifier que le contrat existe et est signé
            contract = self.db.query(Contract).filter(Contract.id == contract_id).first()
            if not contract:
                raise ValidationError("Contrat non trouvé")

            if not contract.signed or contract.status != ContractStatus.SIGNED:
                raise ValidationError(
                    "Impossible de créer un événement pour un contrat non signé"
                )

            # Seul le commercial du contrat ou la gestion peut créer des événements
            if (self.current_user.is_commercial and
               contract.commercial_contact_id != self.current_user.id and not self.current_user.is_gestion):
                raise AuthorizationError(
                    "Vous ne pouvez créer des événements que pour vos contrats"
                )

            # Créer l'événement
            event = Event(
                contract_id=contract_id,
                name=validated_name,
                start_date=start_date,
                end_date=end_date,
                location=validated_location,
                attendees=validated_attendees,
                notes=notes.strip() if notes else None
            )

            self.db.add(event)
            self.db.commit()
            self.db.refresh(event)
            return event

        except (ValidationError, ValueError) as e:
            self.db.rollback()
            raise ValidationError(str(e))
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erreur lors de la création de l'événement: {e}")

    def update_event(self, event_id: int, **kwargs) -> Event:
        """Modifier un evenement"""
        if not self.permission_checker.has_permission(self.current_user, 'update_event'):
            if not (self.current_user.is_support and
                    self.permission_checker.has_permission(self.current_user, 'update_assigned_event')):
                raise AuthorizationError("Permission requise pour modifier les événements")

        event = self.get_event_by_id(event_id)
        if not event:
            raise ValueError("Événement non trouvé")

        if not self._can_access_event(event):
            raise AuthorizationError("Accès refusé à cet événement")

        try:
            # Validation et mise à jour des champs
            if 'name' in kwargs:
                event.name = self.validator.validate_event_name(kwargs['name'])

            if 'location' in kwargs:
                event.location = self.validator.validate_location(kwargs['location'])

            if 'attendees' in kwargs:
                event.attendees = self.validator.validate_attendees_count(kwargs['attendees'])

            if 'start_date' in kwargs or 'end_date' in kwargs:
                start_date = kwargs.get('start_date', event.start_date)
                end_date = kwargs.get('end_date', event.end_date)

                # Permettre la modification de dates passées pour les événements terminés
                if start_date >= datetime.now():
                    self.validator.validate_date_range(start_date, end_date)
                elif end_date <= start_date:
                    raise ValidationError(
                        "La date de fin doit être postérieure à la date de début"
                    )

                event.start_date = start_date
                event.end_date = end_date

            if 'notes' in kwargs:
                notes = kwargs['notes']
                event.notes = notes.strip() if notes else None

            # Seule la gestion peut changer l'assignation support
            if 'support_contact_id' in kwargs:
                if not self.current_user.is_gestion:
                    raise AuthorizationError(
                        "Seule la gestion peut changer l'assignation support"
                    )

                support_id = kwargs['support_contact_id']
                if support_id is not None:
                    support = self.db.query(User).filter(User.id == support_id).first()
                    if not support or not support.is_support:
                        raise ValidationError("Le contact support spécifié n'existe pas")

                event.support_contact_id = support_id

            # Support ne peut modifier que certains champs
            if self.current_user.is_support and not self.current_user.is_gestion:
                forbidden_fields = ['name', 'start_date', 'end_date', 'contract_id']
                forbidden_updates = set(kwargs.keys()) & set(forbidden_fields)
                if forbidden_updates:
                    raise AuthorizationError(
                        f"Support ne peut pas modifier: {', '.join(forbidden_updates)}"
                    )

            self.db.commit()
            self.db.refresh(event)
            return event

        except (ValidationError, ValueError) as e:
            self.db.rollback()
            raise ValidationError(str(e))
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erreur lors de la modification de l'événement: {e}")

    def assign_support_to_event(self, event_id: int, support_user_id: int) -> Event:
        """Assigner un support a un evenement"""
        if not self.current_user.is_gestion:
            raise AuthorizationError("Seule la gestion peut assigner des supports")

        event = self.get_event_by_id(event_id)
        if not event:
            raise ValueError("Événement non trouvé")

        # Vérifier que l'utilisateur est bien du support
        support_user = self.db.query(User).filter(User.id == support_user_id).first()
        if not support_user or not support_user.is_support:
            raise ValueError("L'utilisateur doit être du département SUPPORT")

        try:
            event.support_contact_id = support_user_id
            self.db.commit()
            self.db.refresh(event)
            return event
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erreur lors de l'assignation: {e}")

    def get_all_events(self) -> List[Event]:
        """Recuperer tous les evenements avec verification des permissions"""
        if not self.permission_checker.has_permission(self.current_user, 'read_event'):
            raise AuthorizationError("Permission requise pour consulter les événements")

        # Seule la gestion peut voir TOUS les evenements
        if not self.current_user.is_gestion:
            raise AuthorizationError("Seule la gestion peut consulter tous les événements")

        return self.db.query(Event).options(
            joinedload(Event.contract).joinedload(Contract.client),
            joinedload(Event.contract).joinedload(Contract.commercial_contact),
            joinedload(Event.support_contact)
        ).all()

    def get_event_by_id(self, event_id: int) -> Optional[Event]:
        """Recuperer un evenement par son ID avec verification d'acces"""
        if not self.permission_checker.has_permission(self.current_user, 'read_event'):
            raise AuthorizationError("Permission requise pour consulter les événements")

        event = self.db.query(Event).options(
            joinedload(Event.contract).joinedload(Contract.client),
            joinedload(Event.contract).joinedload(Contract.commercial_contact),
            joinedload(Event.support_contact)
        ).filter(Event.id == event_id).first()

        if event and not self._can_access_event(event):
            raise AuthorizationError("Accès refusé à cet événement")

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
            raise AuthorizationError("Rôle non autorisé")

        return query.all()

    def get_upcoming_events(self, days_ahead: int = 30) -> List[Event]:
        """Recuperer les evenements a venir selon les permissions"""
        if not self.permission_checker.has_permission(self.current_user, 'read_event'):
            raise AuthorizationError("Permission requise pour consulter les événements")

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
            raise AuthorizationError("Rôle non autorisé")

        return query.order_by(Event.start_date).all()

    def get_events_without_support(self) -> List[Event]:
        """Recuperer les evenements sans support assigne"""
        if not self.permission_checker.has_permission(self.current_user, 'read_event'):
            raise AuthorizationError("Permission requise pour consulter les événements")

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
            # Support peut voir tous les evenements non assignes
            pass
        elif not self.current_user.is_gestion:
            raise AuthorizationError("Rôle non autorisé")

        return query.all()

    def search_events(self, **criteria) -> List[Event]:
        """Rechercher des evenements selon des criteres et permissions"""
        if not self.permission_checker.has_permission(self.current_user, 'read_event'):
            raise AuthorizationError("Permission requise pour consulter les événements")

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
            raise AuthorizationError("Rôle non autorisé")

        return query.all()

    def _can_access_event(self, event: Event) -> bool:
        """Verifier si l'utilisateur peut acceder a cet evenement"""
        if self.current_user.is_gestion:
            return True

        if self.current_user.is_support:
            return event.support_contact_id == self.current_user.id

        if self.current_user.is_commercial:
            return event.contract.commercial_contact_id == self.current_user.id

        return False
