"""
Contrôleur de gestion des contrats pour Epic Events CRM

Ce module implémente la logique métier pour la gestion complète des contrats
commerciaux dans le système Epic Events. Il applique le pattern MVC en
centralisant toutes les opérations CRUD sur les contrats avec validation
complète et gestion des permissions par rôle.

Fonctionnalités principales:
- Création de contrats avec validation des montants et clients
- Modification des contrats existants avec contrôle d'intégrité
- Consultation des contrats avec filtrage selon les permissions
- Signature électronique des contrats avec traçabilité
- Gestion des statuts (brouillon, signé, annulé)

Architecture Pattern MVC:
- Modèle: Contract, Client (entités métier)
- Vue: Interface CLI ou API (séparée)
- Contrôleur: ContractController (ce fichier - logique métier)

Permissions par département:
- COMMERCIAL: Création/modification de ses propres contrats clients
- GESTION: Accès complet à tous les contrats + signature
- SUPPORT: Lecture seule des contrats avec événements assignés

Règles métier implémentées:
- Montant dû ≤ montant total (validation financière)
- Commercial responsable = commercial du client (cohérence)
- Signature uniquement par la gestion (autorisation)
- Traçabilité complète des modifications (audit)

Fichier: src/controllers/contract_controller.py
Auteur: Epic Events CRM Team
Date: 2024
Version: 1.0
"""

from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session, joinedload
from src.models.contract import Contract, ContractStatus
from src.models.client import Client
from src.utils.auth_utils import AuthorizationError
from src.utils.validators import ValidationError
from src.services.logging_service import SentryLogger
from .base_controller import BaseController


class ContractController(BaseController):
    """
    Contrôleur spécialisé pour la gestion des contrats commerciaux Epic Events

    Cette classe implémente toute la logique métier liée aux contrats dans
    le système CRM. Elle hérite de BaseController pour bénéficier des
    fonctionnalités communes (permissions, validation, transactions).

    Responsabilités:
    - Validation des données contractuelles (montants, statuts, clients)
    - Application des règles métier (cohérence commercial/client)
    - Gestion des permissions par département
    - Traçabilité des opérations pour audit
    - Intégration avec le système de logging Sentry

    Attributs:
        db (Session): Session SQLAlchemy héritée pour accès base de données
        current_user (User): Utilisateur connecté pour contrôle permissions
        permission_checker (PermissionChecker): Vérificateur de permissions
        validator (DataValidator): Validateur de données métier
        sentry_logger (SentryLogger): Logger pour traçabilité et monitoring

    Note:
        Utilise les transactions automatiques SQLAlchemy avec rollback
        en cas d'erreur pour maintenir l'intégrité des données.
    """

    def __init__(self, db_session: Session):
        """
        Initialise le contrôleur de contrats avec session base de données

        Configure tous les composants nécessaires pour les opérations
        sur les contrats : validation, permissions, logging.

        Args:
            db_session (Session): Session SQLAlchemy active pour les opérations DB

        Note:
            L'utilisateur current_user doit être défini via set_current_user()
            avant d'effectuer des opérations nécessitant des permissions.
        """
        # Initialisation du contrôleur de base (permissions, validation, DB)
        super().__init__(db_session)

        # Ajout du logger Sentry pour traçabilité spécifique aux contrats
        self.sentry_logger = SentryLogger()

    def create_contract(self, client_id: int, total_amount: float,
                        amount_due: float = None) -> Contract:
        """
        Créer un nouveau contrat avec validation complète des données

        Cette méthode centralise la création sécurisée de nouveaux contrats
        en appliquant toutes les règles métier et validations nécessaires.

        Args:
            client_id (int): Identifiant du client pour lequel créer le contrat
            total_amount (float): Montant total du contrat en euros
            amount_due (float, optional): Montant encore dû. Si None, égal au total

        Returns:
            Contract: Nouveau contrat créé avec statut DRAFT par défaut

        Raises:
            AuthorizationError: Si l'utilisateur n'a pas la permission 'create_contract'
            ValidationError: Si les données ne respectent pas les règles métier:
                - Montants négatifs ou invalides
                - Montant dû > montant total
                - Client inexistant

        Règles métier appliquées:
        - Seuls COMMERCIAL et GESTION peuvent créer des contrats
        - Le commercial responsable est automatiquement celui du client
        - Statut initial toujours DRAFT (brouillon)
        - Montant dû par défaut = montant total (contrat non payé)
        - Validation stricte des montants (positifs, cohérents)

        Exemple:
            >>> contract = controller.create_contract(
            ...     client_id=123,
            ...     total_amount=10000.0,
            ...     amount_due=8000.0
            ... )
        """
        # === VÉRIFICATION DES PERMISSIONS ===
        # Seuls COMMERCIAL et GESTION peuvent créer des contrats
        self.require_create_access('contract')

        # === VALIDATION DES MONTANTS AVEC RÈGLES MÉTIER ===
        try:
            # Validation du montant total (doit être positif et réaliste)
            validated_total_amount = self.validator.validate_amount(
                total_amount, "Montant total"
            )

            # Gestion du montant dû avec valeur par défaut
            if amount_due is not None:
                validated_amount_due = self.validator.validate_amount(
                    amount_due, "Montant dû"
                )
            else:
                # Par défaut, montant dû = montant total (contrat non payé)
                validated_amount_due = validated_total_amount

            # Règle métier critique : montant dû ≤ montant total
            if validated_amount_due > validated_total_amount:
                raise ValidationError("Le montant dû ne peut pas être supérieur au montant total")

        except ValidationError as e:
            # Re-propagation avec contexte pour débogage
            raise ValidationError(f"Validation des montants: {e}")

        # === VÉRIFICATION EXISTENCE CLIENT ===
        # Le contrat doit être lié à un client existant
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise ValidationError("Client non trouvé")

        # === CRÉATION DU CONTRAT AVEC TRANSACTION SÉCURISÉE ===
        try:
            # Création de l'objet Contract avec toutes les données validées
            contract = Contract(
                client_id=client_id,
                total_amount=validated_total_amount,
                amount_due=validated_amount_due,
                status=ContractStatus.DRAFT,  # Statut initial obligatoire
                # Héritage automatique du commercial responsable du client
                commercial_contact_id=client.commercial_contact_id
            )

            # Ajout à la session SQLAlchemy pour persistence
            self.db.add(contract)

            # Sauvegarde sécurisée avec gestion d'erreur intégrée
            self.safe_commit()

            # Actualisation de l'objet avec les données DB (ID auto-généré)
            self.db.refresh(contract)

            # Retour du contrat créé avec son ID assigné
            return contract

        except Exception as e:
            # Rollback automatique pour maintenir intégrité
            self.db.rollback()
            raise Exception(f"Erreur lors de la création: {e}")

    def update_contract(self, contract_id: int, **update_data) -> Contract:
        """
        Mettre à jour un contrat existant avec validation complète

        Permet la modification des contrats selon les permissions utilisateur
        avec validation de toutes les règles métier et traçabilité complète.

        Args:
            contract_id (int): Identifiant du contrat à modifier
            **update_data: Données à modifier (total_amount, amount_due, status, etc.)

        Returns:
            Contract: Contrat modifié avec nouvelles valeurs

        Raises:
            ValidationError: Si contrat inexistant ou données invalides
            AuthorizationError: Si l'utilisateur n'a pas les permissions

        Permissions:
        - COMMERCIAL: Peut modifier ses propres contrats (même commercial que client)
        - GESTION: Peut modifier tous les contrats
        - SUPPORT: Lecture seule (pas de modification)

        Champs modifiables:
        - total_amount: Montant total du contrat
        - amount_due: Montant encore dû
        - status: Statut du contrat (DRAFT, SIGNED, CANCELLED)

        Règles métier:
        - Montant dû ≤ montant total (cohérence financière)
        - Signature = logging automatique pour audit
        - Champs système protégés (id, client_id, commercial_contact_id)
        """
        # === RÉCUPÉRATION ET VÉRIFICATION EXISTENCE ===
        contract = self.get_contract_by_id(contract_id)
        if not contract:
            raise ValidationError("Contrat non trouvé")

        # === VÉRIFICATION DES PERMISSIONS D'ÉCRITURE ===
        # Contrôle selon le département et propriété du contrat
        self.require_write_access('contract', contract)

        # === VALIDATION DES DONNÉES DE MISE À JOUR ===
        try:
            validated_data = {}

            # === VALIDATION DES MONTANTS FINANCIERS ===
            # Validation du montant total si fourni
            if 'total_amount' in update_data:
                validated_data['total_amount'] = self.validator.validate_amount(
                    update_data['total_amount'], "Montant total"
                )

            # Validation du montant dû si fourni
            if 'amount_due' in update_data:
                validated_data['amount_due'] = self.validator.validate_amount(
                    update_data['amount_due'], "Montant dû"
                )

            # === VÉRIFICATION RÈGLE MÉTIER CRITIQUE ===
            # Le montant dû ne peut jamais dépasser le montant total
            total = validated_data.get('total_amount', contract.total_amount)
            due = validated_data.get('amount_due', contract.amount_due)

            if due > total:
                raise ValidationError("Le montant dû ne peut pas être supérieur au montant total")

            # === VALIDATION DU STATUT ET TRAÇABILITÉ ===
            if 'status' in update_data:
                if isinstance(update_data['status'], str):
                    validated_data['status'] = self.validator.validate_contract_status(
                        update_data['status']
                    )
                else:
                    validated_data['status'] = update_data['status']

                # Détection d'une signature de contrat pour logging spécial
                is_being_signed = (
                    validated_data['status'] == ContractStatus.SIGNED and
                    contract.status != ContractStatus.SIGNED
                )

            # === APPLICATION DES MISES À JOUR AVEC PROTECTION ===
            # Champs système protégés contre modification accidentelle
            forbidden_fields = ['id', 'client_id', 'commercial_contact_id',
                                'created_at', 'updated_at']
            self.apply_validated_updates(contract, validated_data, forbidden_fields)

            # Sauvegarde sécurisée en base de données
            self.safe_commit()
            self.db.refresh(contract)

            # === LOGGING SPÉCIAL POUR SIGNATURES DE CONTRATS ===
            # Traçabilité obligatoire pour audit et conformité
            if 'status' in validated_data and is_being_signed:
                print(f"    - Client: {getattr(contract.client, 'company_name', 'NON CHARGÉ')}")
                print(f"    - Commercial: {getattr(self.current_user, 'full_name', 'NON DÉFINI')}")
                try:
                    # Force le chargement des relations pour le logging
                    self.db.refresh(contract)
                    self.sentry_logger.log_contract_signature(contract, self.current_user)
                except Exception as e:
                    print(f"ERREUR lors du log: {e}")
                    import traceback
                    traceback.print_exc()

            return contract

        except ValidationError:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erreur lors de la mise à jour: {e}")

    def get_all_contracts(self) -> List[Contract]:
        """
        Récupérer tous les contrats du système (accès GESTION uniquement)

        Cette méthode permet aux gestionnaires d'accéder à la liste complète
        de tous les contrats de l'entreprise pour supervision et reporting.

        Returns:
            List[Contract]: Liste complète de tous les contrats avec relations

        Raises:
            AuthorizationError: Si l'utilisateur n'est pas du département GESTION

        Permissions:
        - GESTION: Accès complet à tous les contrats
        - COMMERCIAL/SUPPORT: Accès refusé (doivent utiliser get_my_contracts)

        Relations incluses:
        - Client associé au contrat
        - Commercial responsable du contrat

        Usage:
            Pour génération de rapports globaux et supervision managériale
        """
        # Vérification permission de lecture générique
        self.require_read_access('contract')

        # Restriction stricte : seule la GESTION a accès global
        if not self.current_user.is_gestion:
            raise AuthorizationError("Seule la gestion peut consulter tous les contrats")

        # Récupération avec eager loading des relations importantes
        return self.db.query(Contract).options(
            joinedload(Contract.client),             # Client pour infos entreprise
            joinedload(Contract.commercial_contact)  # Commercial pour suivi
        ).all()

    def get_contract_by_id(self, contract_id: int) -> Optional[Contract]:
        """Recuperer un contrat par son ID avec verification d'acces"""
        self.require_read_access('contract')

        contract = self.db.query(Contract).options(
            joinedload(Contract.client),
            joinedload(Contract.commercial_contact),
            joinedload(Contract.events)
        ).filter(Contract.id == contract_id).first()

        if contract and not self._can_access_contract(contract):
            raise AuthorizationError("Accès refusé à ce contrat")

        return contract

    def get_my_contracts(self) -> List[Contract]:
        """Recuperer les contrats assignes a l'utilisateur actuel"""
        if not self.current_user:
            raise AuthorizationError("Authentification requise")

        if not self.current_user.is_commercial:
            raise AuthorizationError("Seuls les commerciaux peuvent consulter leurs contrats")

        return self.db.query(Contract).options(
            joinedload(Contract.client),
            joinedload(Contract.commercial_contact),
            joinedload(Contract.events)
        ).filter(Contract.commercial_contact_id == self.current_user.id).all()

    def sign_contract(self, contract_id: int) -> Contract:
        """
        Signer électroniquement un contrat (GESTION uniquement)

        Effectue la signature officielle d'un contrat en changeant son statut
        de DRAFT vers SIGNED avec traçabilité complète de l'opération.

        Args:
            contract_id (int): Identifiant du contrat à signer

        Returns:
            Contract: Contrat signé avec statut mis à jour

        Raises:
            ValidationError: Si contrat inexistant ou déjà signé
            AuthorizationError: Si l'utilisateur n'est pas GESTION

        Permissions:
        - GESTION: Seul département autorisé à signer
        - COMMERCIAL/SUPPORT: Accès refusé

        Règles métier:
        - Seuls les contrats DRAFT peuvent être signés
        - Signature = changement de statut irréversible
        - Logging automatique pour audit et traçabilité

        Traçabilité:
        - Enregistrement Sentry de la signature
        - Informations: qui, quand, quel contrat
        - Données client et commercial pour contexte
        """
        # === RÉCUPÉRATION ET VALIDATION EXISTENCE ===
        contract = self.get_contract_by_id(contract_id)
        if not contract:
            raise ValidationError("Contrat non trouvé")

        # Seule la gestion peut signer des contrats
        if not self.current_user.is_gestion:
            raise AuthorizationError("Seule la gestion peut signer des contrats")

        if contract.status == ContractStatus.SIGNED:
            raise ValidationError("Ce contrat est déjà signé")

        contract.status = ContractStatus.SIGNED
        contract.signed = True  # Ajouter cette ligne
        contract.signed_date = datetime.now(timezone.utc)

        self.safe_commit()
        self.db.refresh(contract)

        # Journaliser la signature
        try:
            self.sentry_logger.log_contract_signature(contract, self.current_user)
        except Exception as e:
            print(f"Erreur lors du log de signature: {e}")

        return contract

    def delete_contract(self, contract_id: int) -> bool:
        """Supprimer un contrat"""
        contract = self.get_contract_by_id(contract_id)
        if not contract:
            raise ValidationError("Contrat non trouvé")

        # Seule la gestion peut supprimer des contrats
        if not self.current_user.is_gestion:
            raise AuthorizationError("Seule la gestion peut supprimer des contrats")

        # Vérifier qu'il n'y a pas d'événements associés
        if contract.events:
            raise ValidationError("Impossible de supprimer un contrat avec des événements associés")

        try:
            self.db.delete(contract)
            self.safe_commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erreur lors de la suppression: {e}")

        return self.db.query(Contract).options(
            joinedload(Contract.client),
            joinedload(Contract.commercial_contact)
        ).filter(Contract.commercial_contact_id == self.current_user.id).all()

    def get_contracts_by_status(self, status: ContractStatus) -> List[Contract]:
        """Recuperer les contrats par statut"""
        if not self.permission_checker.has_permission(self.current_user, 'read_contract'):
            raise AuthorizationError("Permission requise pour consulter les contrats")

        query = self.db.query(Contract).options(
            joinedload(Contract.client),
            joinedload(Contract.commercial_contact)
        ).filter(Contract.status == status)

        # Filtre par role utilisateur
        if self.current_user.is_commercial:
            query = query.filter(Contract.commercial_contact_id == self.current_user.id)
        elif self.current_user.is_support:
            # Support peut voir les contrats avec des evenements assignes
            from src.models.event import Event
            query = query.join(Event).filter(Event.support_contact_id == self.current_user.id)

        return query.all()

    def get_unsigned_contracts(self) -> List[Contract]:
        """Recuperer les contrats non signes"""
        return self.get_contracts_by_status(ContractStatus.DRAFT)

    def get_unpaid_contracts(self) -> List[Contract]:
        """Recuperer les contrats avec des montants dus"""
        if not self.permission_checker.has_permission(self.current_user, 'read_contract'):
            raise AuthorizationError("Permission requise pour consulter les contrats")

        query = self.db.query(Contract).options(
            joinedload(Contract.client),
            joinedload(Contract.commercial_contact)
        ).filter(Contract.amount_due > 0)

        # Filtre par role utilisateur
        if self.current_user.is_commercial:
            query = query.filter(Contract.commercial_contact_id == self.current_user.id)
        elif self.current_user.is_support:
            from src.models.event import Event
            query = query.join(Event).filter(Event.support_contact_id == self.current_user.id)

        return query.all()

    def search_contracts(self, **criteria) -> List[Contract]:
        """Rechercher des contrats selon des criteres"""
        if not self.permission_checker.has_permission(self.current_user, 'read_contract'):
            raise AuthorizationError("Permission requise pour consulter les contrats")

        query = self.db.query(Contract).options(
            joinedload(Contract.client),
            joinedload(Contract.commercial_contact)
        )

        # Filtre par client
        if 'client_name' in criteria and criteria['client_name']:
            query = query.join(Client).filter(
                Client.full_name.ilike(f"%{criteria['client_name']}%")
            )

        # Filtre par entreprise
        if 'company_name' in criteria and criteria['company_name']:
            query = query.join(Client).filter(
                Client.company_name.ilike(f"%{criteria['company_name']}%")
            )

        # Filtre par statut
        if 'status' in criteria and criteria['status']:
            query = query.filter(Contract.status == criteria['status'])

        # Filtre par role utilisateur
        if self.current_user.is_commercial:
            query = query.filter(Contract.commercial_contact_id == self.current_user.id)
        elif self.current_user.is_support:
            from src.models.event import Event
            query = query.join(Event).filter(Event.support_contact_id == self.current_user.id)

        return query.all()

    def _can_access_contract(self, contract: Contract) -> bool:
        """Verifier si l'utilisateur peut acceder a ce contrat"""
        if self.current_user.is_gestion:
            return True

        if self.current_user.is_commercial:
            return contract.commercial_contact_id == self.current_user.id

        if self.current_user.is_support:
            # Support peut voir les contrats avec des evenements assignes
            return any(event.support_contact_id == self.current_user.id for event in contract.events)

        return False
