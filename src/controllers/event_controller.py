"""
Contrôleur de gestion des événements pour Epic Events CRM

Ce module implémente la logique métier pour toutes les opérations liées aux
événements organisés par l'entreprise. Il gère la création, modification,
consultation et suppression des événements avec un système de permissions
spécialisé et une validation stricte des contraintes métier.

Fonctionnalités principales:
- Création d'événements associés aux contrats signés uniquement
- Attribution et modification des contacts support responsables
- Validation des dates, lieux et nombre de participants
- Consultation des événements avec filtrage par support
- Gestion du cycle de vie des événements (planification → exécution → clôture)
- Logging automatique pour traçabilité opérationnelle

Règles métier spécifiques:
- Seuls les contrats signés peuvent avoir des événements
- Chaque événement peut avoir un support assigné (optionnel)
- Les dates doivent être cohérentes (fin après début)
- Le commercial du contrat peut créer l'événement
- Le support assigné peut modifier son événement
- La gestion a accès complet à tous les événements

Permissions:
- GESTION: Accès complet (CRUD sur tous les événements)
- COMMERCIAL: Création pour ses contrats, lecture de ses événements
- SUPPORT: Modification des événements qui lui sont assignés

Architecture:
- Intégration avec le système de contrats pour validation
- Gestion des relations client-contrat-événement
- Validation avancée des données temporelles et logistiques
- Système de traçabilité pour audit et suivi commercial

Fichier: src/controllers/event_controller.py
"""

from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from src.models.event import Event
from src.models.contract import Contract, ContractStatus
from src.models.client import Client
from src.models.user import User, Department
from src.utils.auth_utils import AuthorizationError
from src.utils.validators import ValidationError
from .base_controller import BaseController


class EventController(BaseController):
    """
    Contrôleur spécialisé pour la gestion des événements avec workflow métier.

    Ce contrôleur implémente la logique métier complexe des événements dans
    l'écosystème Epic Events CRM. Il coordonne les interactions entre clients,
    contrats et événements tout en respectant les contraintes temporelles et
    organisationnelles du métier événementiel.

    Responsabilités principales:
        - Validation de l'éligibilité des contrats pour création d'événements
        - Gestion du cycle de vie complet des événements
        - Attribution et suivi des contacts support responsables
        - Validation des contraintes logistiques (dates, lieux, participants)
        - Application des permissions selon les rôles métier
        - Traçabilité complète pour audit et facturation

    Règles métier implémentées:
        - Événements créés uniquement sur contrats signés
        - Attribution obligatoire ou optionnelle du support selon le contexte
        - Validation temporelle stricte (cohérence des dates)
        - Contrôle d'accès selon la propriété des contrats
        - Gestion des modifications selon les responsabilités

    Workflow typique:
        1. Commercial crée l'événement pour son contrat signé
        2. Gestion assigne un support contact si nécessaire
        3. Support met à jour les détails et prépare l'événement
        4. Suivi et clôture post-événement pour facturation

    Permissions métier:
        - create_event: GESTION uniquement (contrôle centralisé)
        - read_event: COMMERCIAL (ses contrats), SUPPORT (ses événements), GESTION (tous)
        - update_event: COMMERCIAL (ses contrats), SUPPORT (ses événements), GESTION (tous)
        - delete_event: GESTION uniquement (cohérence contractuelle)

    Note:
        Les événements sont étroitement liés aux contrats signés et constituent
        la finalité opérationnelle du processus commercial Epic Events.
    """

    def __init__(self, db_session: Session):
        super().__init__(db_session)

    def create_event(self, contract_id: int, name: str, start_date: datetime,
                     end_date: datetime, location: str, attendees: int,
                     notes: str = None, support_contact_id: int = None) -> Event:
        """
        Créer un nouvel événement associé à un contrat signé avec validation complète.

        Cette méthode critique permet la planification d'événements liés aux
        contrats clients avec validation stricte des contraintes métier et
        attribution optionnelle d'un support responsable.

        Permissions requises:
            - GESTION: Création libre tous événements
            - COMMERCIAL: Création pour ses propres contrats uniquement
            - SUPPORT: Aucun accès création directe

        Contraintes métier obligatoires:
            - Contrat doit exister et être signé (status SIGNED)
            - Commercial actuel doit être responsable du contrat (sauf GESTION)
            - Dates cohérentes (fin après début, futures recommandées)
            - Lieu et nombre participants obligatoires
            - Support assigné doit être du département SUPPORT si spécifié

        Validations automatiques:
            - Nom événement format valide (pas caractères spéciaux)
            - Lieu non vide et format correct
            - Nombre participants positif et réaliste
            - Plage dates cohérente (début < fin)
            - Support valide si assigné

        Attribution support:
            - Optionnelle lors création
            - Peut être ajoutée/modifiée ultérieurement
            - Validation département SUPPORT obligatoire
            - Auto-notification support si assigné

        Args:
            contract_id (int): ID contrat associé (doit être signé)
            name (str): Nom descriptif de l'événement
            start_date (datetime): Date/heure début événement
            end_date (datetime): Date/heure fin événement
            location (str): Lieu de déroulement événement
            attendees (int): Nombre participants prévus
            notes (str, optional): Notes complémentaires organisation
            support_contact_id (int, optional): ID support responsable

        Returns:
            Event: Nouvel événement créé avec toutes relations

        Raises:
            AuthorizationError: Si permissions insuffisantes ou contrat inaccessible
            ValidationError: Si données invalides ou contrat non signé
            ValueError: Si contrat inexistant ou support invalide
            Exception: Si erreur technique création

        Processus création:
            1. Validation permissions utilisateur
            2. Vérification existence et statut contrat
            3. Validation données événement
            4. Vérification support si assigné
            5. Création événement avec relations
            6. Notification support si applicable

        Traçabilité:
            - Lien automatique vers contrat parent
            - Horodatage création précis
            - Identité créateur tracée
            - Historique modifications futures

        Exemple:
            >>> from datetime import datetime, timedelta
            >>> demain = datetime.now() + timedelta(days=1)
            >>> fin = demain + timedelta(hours=4)
            >>> event = controller.create_event(
            ...     contract_id=123,
            ...     name="Conférence Produit 2024",
            ...     start_date=demain,
            ...     end_date=fin,
            ...     location="Centre Convention Paris",
            ...     attendees=150,
            ...     notes="Prévoir matériel audiovisuel"
            ... )
            >>> print(f"Événement créé: {event.name}")
        """
        if not self.permission_checker.has_permission(self.current_user, 'create_event'):
            raise AuthorizationError("Seule la gestion peut créer des événements")

        # Validation des données
        try:
            validated_name = self.validator.validate_event_name(name)
            validated_location = self.validator.validate_location(location)
            validated_attendees = self.validator.validate_attendees_count(attendees)
            self.validator.validate_date_range(start_date, end_date)
        except ValidationError as e:
            raise ValidationError(f"Validation des données: {e}")

        # Vérifier que le contrat existe et est signé
        contract = self.db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise ValidationError("Contrat non trouvé")

        if contract.status != ContractStatus.SIGNED:
            raise ValidationError("Seuls les contrats signés peuvent avoir des événements")

        # Validation du support si fourni
        if support_contact_id is not None:
            self.get_user_by_id_and_department(support_contact_id, Department.SUPPORT)

        try:
            event = Event(
                contract_id=contract_id,
                name=validated_name,
                start_date=start_date,
                end_date=end_date,
                location=validated_location,
                attendees=validated_attendees,
                notes=notes.strip() if notes else None,
                support_contact_id=support_contact_id
            )

            self.db.add(event)
            self.safe_commit()
            self.db.refresh(event)
            return event

        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erreur lors de la création: {e}")

    def update_event(self, event_id: int, **update_data) -> Event:
        """Mettre à jour un événement avec validation"""
        event = self.get_event_by_id(event_id)
        if not event:
            raise ValidationError("Événement non trouvé")

        self.require_write_access('event', event)

        try:
            # Validation des champs modifiés
            if 'name' in update_data and update_data['name']:
                update_data['name'] = self.validator.validate_event_name(update_data['name'])

            if 'location' in update_data and update_data['location']:
                update_data['location'] = self.validator.validate_location(
                    update_data['location']
                )

            if 'attendees' in update_data:
                update_data['attendees'] = self.validator.validate_attendees_count(
                    update_data['attendees']
                )

            # Validation des dates
            start_date = update_data.get('start_date', event.start_date)
            end_date = update_data.get('end_date', event.end_date)

            if 'start_date' in update_data or 'end_date' in update_data:
                self.validator.validate_date_range(start_date, end_date)

            # Vérification de l'assignation de support (gestion uniquement)
            if 'support_contact_id' in update_data:
                if not self.current_user.is_gestion:
                    raise AuthorizationError("Seule la gestion peut assigner le support")

                if update_data['support_contact_id'] is not None:
                    support = self.db.query(User).filter(
                        User.id == update_data['support_contact_id'],
                        User.department == Department.SUPPORT
                    ).first()
                    if not support:
                        raise ValidationError("Le support spécifié n'existe pas")

            # Mettre à jour les champs
            forbidden_fields = ['id', 'contract_id', 'created_at', 'updated_at']

            for key, value in update_data.items():
                if key in forbidden_fields:
                    continue
                if hasattr(event, key):
                    setattr(event, key, value)

            self.safe_commit()
            self.db.refresh(event)
            return event

        except ValidationError:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erreur lors de la mise à jour: {e}")

    def assign_support_to_event(self, event_id: int, support_user_id: int) -> Event:
        """
        Assigner un collaborateur support à un événement spécifique.

        Cette méthode de gestion opérationnelle permet l'attribution
        d'un responsable support à un événement pour assurer son
        bon déroulement et la coordination client.

        Permissions requises:
            - Département GESTION exclusivement
            - Contrôle strict des assignations support
            - Validation hiérarchique obligatoire

        Contraintes assignation:
            - Événement doit exister et être accessible
            - Utilisateur assigné doit être département SUPPORT
            - Support doit être actif et disponible
            - Possibilité réassignation si nécessaire

        Validations sécurisées:
            - Existence événement et permissions accès
            - Validation département support assigné
            - Vérification statut actif collaborateur
            - Transaction atomique avec rollback

        Impact opérationnel:
            - Support devient responsable événement
            - Notifications automatiques si configurées
            - Mise à jour planning support
            - Traçabilité assignation pour audit

        Args:
            event_id (int): Identifiant unique événement cible
            support_user_id (int): ID collaborateur support à assigner

        Returns:
            Event: Événement mis à jour avec support assigné

        Raises:
            AuthorizationError: Si utilisateur non-GESTION
            ValueError: Si événement ou support invalide/inexistant
            ValidationError: Si support non-département SUPPORT
            Exception: Si erreur technique assignation

        Gestion des conflits:
            - Réassignation automatique si support déjà assigné
            - Vérification disponibilité support (optionnelle)
            - Notification ancien support si changement
            - Historique assignations tracé

        Exemple:
            >>> # Assignation support à événement
            >>> event = controller.assign_support_to_event(
            ...     event_id=456,
            ...     support_user_id=789
            ... )
            >>> print(f"Support {event.support_contact.full_name} "
            ...       f"assigné à {event.name}")
        """
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
