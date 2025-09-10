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
        """
        Récupérer un contrat spécifique par son identifiant avec contrôle d'accès.

        Cette méthode permet de récupérer un contrat unique en appliquant
        automatiquement les règles de permissions selon le département utilisateur.

        Contrôle d'accès par département:
            - GESTION: Accès à tous les contrats système
            - COMMERCIAL: Accès uniquement aux contrats de leurs clients
            - SUPPORT: Accès aux contrats liés à leurs événements assignés

        Relations chargées automatiquement:
            - Client associé au contrat (informations entreprise)
            - Commercial responsable (coordonnées et suivi)
            - Événements liés (pour validation support)

        Args:
            contract_id (int): Identifiant unique du contrat à récupérer

        Returns:
            Optional[Contract]: Contrat trouvé avec relations ou None si inexistant/inaccessible

        Raises:
            AuthorizationError: Si l'utilisateur n'a pas accès à ce contrat spécifique

        Exemple:
            >>> contract = controller.get_contract_by_id(123)
            >>> if contract:
            ...     print(f"Contrat {contract.id} - Client: {contract.client.full_name}")
        """
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
        """
        Récupérer les contrats assignés à l'utilisateur commercial connecté.

        Cette méthode spécialisée permet aux commerciaux de consulter
        uniquement les contrats dont ils sont responsables.

        Restrictions d'accès:
            - Réservé exclusivement au département COMMERCIAL
            - Filtrage automatique par commercial_contact_id
            - Authentification utilisateur obligatoire

        Relations incluses:
            - Client: Informations complètes de l'entreprise cliente
            - Commercial: Données du responsable commercial (soi-même)
            - Événements: Liste des événements liés aux contrats

        Returns:
            List[Contract]: Liste des contrats assignés au commercial connecté

        Raises:
            AuthorizationError: Si utilisateur non authentifié ou non-commercial

        Usage typique:
            Utilisé par l'interface commercial pour afficher le portefeuille
            client et le suivi des affaires en cours.

        Exemple:
            >>> mes_contrats = controller.get_my_contracts()
            >>> print(f"Je gère {len(mes_contrats)} contrats")
        """
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
        """
        Supprimer définitivement un contrat du système (GESTION uniquement).

        Cette méthode critique permet la suppression complète d'un contrat
        avec vérifications de sécurité et contraintes d'intégrité.

        Restrictions strictes:
            - Réservé exclusivement au département GESTION
            - Impossible si des événements sont associés au contrat
            - Vérification existence obligatoire avant suppression
            - Transaction sécurisée avec rollback automatique

        Contraintes d'intégrité:
            - Aucun événement ne doit être lié au contrat
            - Vérification des dépendances avant suppression
            - Préservation cohérence base de données

        Args:
            contract_id (int): Identifiant du contrat à supprimer

        Returns:
            bool: True si suppression réussie, False sinon

        Raises:
            ValidationError: Si contrat inexistant ou a des événements liés
            AuthorizationError: Si utilisateur non autorisé (non-GESTION)
            Exception: Si erreur technique lors de la suppression

        Sécurité:
            Opération irréversible nécessitant validation manuelle
            et permissions administratives maximales.

        Exemple:
            >>> success = controller.delete_contract(123)
            >>> if success:
            ...     print("Contrat supprimé avec succès")
        """
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

    def get_contracts_by_status(self, status: ContractStatus) -> List[Contract]:
        """
        Récupérer tous les contrats ayant un statut spécifique.

        Cette méthode de filtrage permet de récupérer les contrats selon
        leur statut avec application automatique des permissions utilisateur.

        Filtrage par statut disponible:
            - DRAFT: Contrats en brouillon (non signés)
            - SIGNED: Contrats signés et validés
            - CANCELLED: Contrats annulés ou résiliés

        Permissions par département:
            - GESTION: Accès à tous les contrats du statut demandé
            - COMMERCIAL: Contrats du statut filtré par leur responsabilité
            - SUPPORT: Contrats du statut avec événements assignés

        Relations chargées:
            - Client associé pour informations entreprise
            - Commercial responsable pour suivi et contact

        Args:
            status (ContractStatus): Statut des contrats à récupérer

        Returns:
            List[Contract]: Liste des contrats correspondant au statut et permissions

        Raises:
            AuthorizationError: Si utilisateur sans permission read_contract

        Usage typique:
            - Suivi des contrats en attente de signature
            - Reporting des contrats validés
            - Gestion des contrats annulés

        Exemple:
            >>> drafts = controller.get_contracts_by_status(ContractStatus.DRAFT)
            >>> print(f"{len(drafts)} contrats en attente de signature")
        """
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
        """
        Récupérer tous les contrats non signés (statut DRAFT).

        Méthode de convenance qui utilise get_contracts_by_status()
        pour récupérer spécifiquement les contrats en attente de signature.

        Cas d'usage principal:
            - Vue managériale des contrats en attente
            - Suivi commercial des affaires à finaliser
            - Relances clients pour signature

        Returns:
            List[Contract]: Contrats avec statut DRAFT selon permissions utilisateur

        Permissions:
            Hérite des mêmes règles que get_contracts_by_status()

        Exemple:
            >>> unsigned = controller.get_unsigned_contracts()
            >>> for contract in unsigned:
            ...     print(f"Contrat {contract.id} - {contract.client.company_name}")
        """
        return self.get_contracts_by_status(ContractStatus.DRAFT)

    def get_unpaid_contracts(self) -> List[Contract]:
        """
        Récupérer tous les contrats avec des montants encore dus.

        Cette méthode spécialisée identifie les contrats nécessitant
        un suivi de recouvrement ou de facturation.

        Critère de sélection:
            - amount_due > 0 (montant encore dû supérieur à zéro)
            - Tous statuts confondus (DRAFT, SIGNED, CANCELLED)

        Applications métier:
            - Suivi commercial des paiements en attente
            - Reporting financier des créances clients
            - Relances de facturation et recouvrement
            - Tableau de bord trésorerie

        Permissions par département:
            - GESTION: Tous les contrats impayés du système
            - COMMERCIAL: Leurs contrats clients avec solde dû
            - SUPPORT: Contrats impayés avec événements assignés

        Relations incluses:
            - Client: Pour coordonnées et relances
            - Commercial: Pour suivi et responsabilité

        Returns:
            List[Contract]: Contrats avec montants dus selon permissions

        Raises:
            AuthorizationError: Si permission read_contract non accordée

        Exemple:
            >>> unpaid = controller.get_unpaid_contracts()
            >>> total_due = sum(c.amount_due for c in unpaid)
            >>> print(f"Créances totales: {total_due} EUR")
        """
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
        """
        Rechercher des contrats selon des critères multiples et flexibles.

        Cette méthode avancée permet une recherche fine dans la base
        de contrats avec combinaison de plusieurs critères de filtrage.

        Critères de recherche disponibles:
            - client_name: Recherche partielle dans le nom du client
            - company_name: Recherche partielle dans le nom de l'entreprise
            - status: Filtrage exact par statut de contrat
            - Extensible pour d'autres critères futurs

        Type de recherche:
            - Recherche ILIKE (insensible à la casse)
            - Correspondance partielle avec caractères génériques
            - Combinaison AND de tous les critères fournis

        Permissions appliquées automatiquement:
            - GESTION: Recherche dans tous les contrats système
            - COMMERCIAL: Recherche limitée à leurs contrats clients
            - SUPPORT: Recherche dans contrats avec événements assignés

        Args:
            **criteria: Critères de recherche sous forme de mots-clés
                - client_name (str): Nom ou partie du nom client
                - company_name (str): Nom ou partie du nom entreprise
                - status (ContractStatus): Statut exact à rechercher

        Returns:
            List[Contract]: Contrats correspondant aux critères et permissions

        Raises:
            AuthorizationError: Si permission read_contract non accordée

        Relations incluses:
            - Client pour informations de recherche et affichage
            - Commercial pour contexte et responsabilité

        Exemples:
            >>> # Recherche par nom client
            >>> results = controller.search_contracts(client_name="Dupont")

            >>> # Recherche combinée
            >>> results = controller.search_contracts(
            ...     company_name="TechCorp",
            ...     status=ContractStatus.SIGNED
            ... )
        """
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
        """
        Vérifier si l'utilisateur connecté peut accéder à un contrat spécifique.

        Cette méthode privée implémente la logique centrale de contrôle
        d'accès aux contrats selon les règles métier departementales.

        Règles d'accès par département:
            - GESTION: Accès complet à tous les contrats (supervision)
            - COMMERCIAL: Accès uniquement aux contrats de leurs clients
            - SUPPORT: Accès aux contrats ayant des événements assignés

        Logique de vérification:
            1. Vérification département GESTION (accès total)
            2. Vérification COMMERCIAL + propriété (commercial_contact_id)
            3. Vérification SUPPORT + événements assignés
            4. Refus par défaut pour autres cas

        Args:
            contract (Contract): Instance du contrat à vérifier

        Returns:
            bool: True si accès autorisé, False sinon

        Note technique:
            Utilise la relation contract.events pour vérifier les assignations
            support sans requête DB supplémentaire grâce au eager loading.

        Utilisation interne:
            Appelée automatiquement par get_contract_by_id() pour
            appliquer les restrictions d'accès avant retour des données.

        Exemple logique:
            >>> # GESTION: toujours True
            >>> # COMMERCIAL: True si contract.commercial_contact_id == user.id
            >>> # SUPPORT: True si au moins un event.support_contact_id == user.id
        """
        if self.current_user.is_gestion:
            return True

        if self.current_user.is_commercial:
            return contract.commercial_contact_id == self.current_user.id

        if self.current_user.is_support:
            # Support peut voir les contrats avec des evenements assignes
            return any(event.support_contact_id == self.current_user.id for event in contract.events)

        return False
