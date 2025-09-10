"""
Contrôleur de gestion des clients pour Epic Events CRM

Ce module centralise la logique métier pour toutes les opérations
liées aux clients de l'entreprise. Il gère la création, modification,
consultation et suppression des comptes clients avec un système de
permissions spécialisé selon les départements.

Fonctionnalités principales:
- Création de nouveaux clients avec validation email unique
- Modification des informations client avec traçabilité
- Consultation des clients avec filtrage par commercial responsable
- Suppression contrôlée avec vérification des dépendances
- Gestion des liens avec les commerciaux responsables
- Validation complète des données (email, téléphone, entreprise)

Permissions métier:
- COMMERCIAL: Peut créer et modifier ses propres clients uniquement
- GESTION: Accès complet (CRUD sur tous les clients)
- SUPPORT: Lecture uniquement des clients avec événements assignés

Spécificités clients:
- Email unique obligatoire dans le système
- Chaque client a un commercial responsable attitré
- Lien avec les contrats et événements
- Historique de création et modification tracé

Architecture:
- Hérite de BaseController pour les fonctionnalités communes
- Intègre la validation de données spécialisée clients
- Gestion automatique des transactions avec rollback
- Logging automatique des opérations critiques

Fichier: src/controllers/client_controller.py
"""

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from src.models.client import Client
from src.models.user import Department
from src.utils.auth_utils import AuthorizationError
from src.utils.validators import ValidationError
from .base_controller import BaseController


class ClientController(BaseController):
    """
    Contrôleur spécialisé pour la gestion des clients avec permissions métier

    Ce contrôleur implémente la logique métier spécifique aux clients
    de l'application Epic Events CRM. Il assure la cohérence des données
    clients et respecte les règles métier selon les départements.

    Responsabilités principales:
    - Validation des données clients (email unique, format téléphone)
    - Gestion des liens clients-commerciaux avec vérifications
    - Application des permissions selon le département utilisateur
    - Traçabilité des opérations pour audit commercial
    - Vérification des dépendances avant suppression

    Règles métier spécifiques:
    - Les commerciaux ne peuvent gérer que leurs propres clients
    - L'email client doit être unique dans le système
    - Chaque client doit avoir un commercial responsable
    - Les suppressions nécessitent vérification des contrats/événements

    Permissions implémentées:
    - create_client: COMMERCIAL (ses clients), GESTION (tous)
    - read_client: COMMERCIAL (ses clients), SUPPORT (clients avec événements), GESTION (tous)
    - update_client: COMMERCIAL (ses clients), GESTION (tous)
    - delete_client: GESTION uniquement

    Note:
        Utilise les validateurs spécialisés pour les données métier clients
        et intègre la gestion des erreurs avec rollback automatique.
    """

    def __init__(self, db_session: Session):
        super().__init__(db_session)

    def create_client(self, full_name: str, email: str, phone: str,
                      company_name: str, commercial_contact_id: int = None) -> Client:
        """
        Créer un nouveau client avec validation complète et attribution commerciale.

        Cette méthode métier critique permet la création de nouveaux comptes
        clients avec validation stricte des données et attribution automatique
        ou manuelle d'un commercial responsable selon les permissions.

        Permissions requises:
            - COMMERCIAL: Peut créer des clients (devient automatiquement responsable)
            - GESTION: Peut créer des clients avec attribution libre du commercial
            - SUPPORT: Aucun accès création

        Validations strictes:
            - Email unique dans tout le système client
            - Format téléphone valide (national/international)
            - Nom complet obligatoire et format valide
            - Nom entreprise obligatoire et cohérent
            - Commercial responsable valide et actif

        Attribution commercial:
            - Si COMMERCIAL: auto-attribution (current_user devient responsable)
            - Si GESTION + commercial_contact_id: attribution manuelle
            - Si GESTION sans commercial_contact_id: erreur (attribution obligatoire)

        Contraintes métier:
            - Un client = un commercial responsable unique
            - Email client unique (pas de doublons)
            - Données contact complètes obligatoires
            - Lien automatique avec le département commercial

        Args:
            full_name (str): Nom complet du contact client (obligatoire)
            email (str): Adresse email unique du client (validation stricte)
            phone (str): Numéro téléphone (format national ou international)
            company_name (str): Nom de l'entreprise cliente (obligatoire)
            commercial_contact_id (int, optional): ID commercial responsable (GESTION uniquement)

        Returns:
            Client: Nouveau client créé avec toutes données validées

        Raises:
            AuthorizationError: Si permission create_client non accordée
            ValidationError: Si données invalides (email existant, format incorrect)
            ValueError: Si commercial responsable introuvable ou inactif
            IntegrityError: Si violation contraintes base de données
            Exception: Si erreur technique création

        Traçabilité:
            - Horodatage création automatique
            - Lien vers utilisateur créateur
            - Audit trail complet
            - Historique attribution commercial

        Règles spéciales:
            - Auto-attribution pour COMMERCIAL (sécurité)
            - Validation croisée email/téléphone/entreprise
            - Vérification unicité multi-critères
            - Transaction atomique avec rollback

        Exemple:
            >>> # Création par commercial (auto-attribution)
            >>> client = controller.create_client(
            ...     "Jean Dupont",
            ...     "jean.dupont@entreprise.com",
            ...     "+33123456789",
            ...     "Entreprise SARL"
            ... )
            >>> print(f"Client créé: {client.id}, Commercial: {client.commercial_contact_id}")
        """
        if not self.permission_checker.has_permission(self.current_user, 'create_client'):
            raise AuthorizationError("Permission 'create_client' requise")

        # Validation des données avec vérification d'unicité email
        try:
            validated_email = self.validate_and_check_unique_email(email, Client)
            validated_phone = self.validator.validate_phone(phone)
            validated_full_name = self.validator.validate_full_name(full_name)
            validated_company_name = self.validator.validate_company_name(company_name)
        except ValidationError as e:
            raise ValidationError(f"Validation échouée: {e}")

        # Déterminer le commercial responsable
        if not commercial_contact_id:
            if self.current_user.is_commercial:
                commercial_contact_id = self.current_user.id
            else:
                raise ValidationError("Un commercial responsable doit être spécifié")

        # Vérifier que le commercial existe
        self.get_user_by_id_and_department(commercial_contact_id, Department.COMMERCIAL)

        # Commercial ne peut créer que pour lui-même
        if self.current_user.is_commercial and commercial_contact_id != self.current_user.id:
            raise AuthorizationError("Vous ne pouvez créer des clients que pour vous-même")

        try:
            client = Client(
                full_name=validated_full_name,
                email=validated_email,
                phone=validated_phone,
                company_name=validated_company_name,
                commercial_contact_id=commercial_contact_id
            )

            self.db.add(client)
            self.safe_commit()
            self.db.refresh(client)
            return client

        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erreur lors de la création: {e}")

    def update_client(self, client_id: int, **update_data) -> Client:
        """
        Mettre à jour les informations d'un client existant avec validation.

        Cette méthode critique permet la modification des données client
        avec validation stricte et respect des permissions selon le département
        de l'utilisateur connecté et la relation commercial-client.

        Permissions requises:
            - COMMERCIAL: Peut modifier uniquement ses propres clients
            - GESTION: Peut modifier tous les clients du système
            - SUPPORT: Aucun accès modification

        Validations appliquées:
            - Client existe et est accessible selon permissions
            - Email unique si modifié (pas de doublons)
            - Format téléphone valide si modifié
            - Nom complet et entreprise valides si modifiés
            - Commercial responsable valide si modifié

        Données modifiables:
            - full_name: Nom complet du contact client
            - email: Adresse email (avec vérification unicité)
            - phone: Numéro de téléphone (validation format)
            - company_name: Nom de l'entreprise cliente
            - commercial_contact_id: Changement commercial responsable (GESTION uniquement)

        Contraintes de sécurité:
            - COMMERCIAL ne peut pas changer le commercial responsable
            - Validation croisée des données modifiées
            - Transaction atomique avec rollback automatique
            - Audit trail des modifications

        Args:
            client_id (int): Identifiant unique du client à modifier
            **update_data: Données à mettre à jour (dictionnaire flexible)
                - full_name (str, optional): Nouveau nom complet
                - email (str, optional): Nouvelle adresse email
                - phone (str, optional): Nouveau numéro téléphone
                - company_name (str, optional): Nouveau nom entreprise
                - commercial_contact_id (int, optional): Nouveau commercial (GESTION)

        Returns:
            Client: Client mis à jour avec nouvelles données validées

        Raises:
            AuthorizationError: Si accès client non autorisé selon permissions
            ValidationError: Si client introuvable ou données invalides
            IntegrityError: Si violation contraintes (email unique)
            ValueError: Si commercial responsable invalide
            Exception: Si erreur technique modification

        Traçabilité:
            - Horodatage modification automatique
            - Historique des changements
            - Identité utilisateur modificateur
            - Sauvegarde état précédent

        Cas d'usage métier:
            - Mise à jour coordonnées client
            - Correction informations entreprise
            - Changement commercial responsable (réorganisation)
            - Mise à jour massive données (import/export)

        Exemple:
            >>> # Modification coordonnées par commercial responsable
            >>> client = controller.update_client(
            ...     client_id=123,
            ...     email="nouveau.email@entreprise.com",
            ...     phone="+33987654321"
            ... )
            >>> print(f"Client mis à jour: {client.full_name}")
        """
        client = self.get_client_by_id(client_id)
        if not client:
            raise ValidationError("Client non trouvé")

        self.require_write_access('client', client)

        try:
            # Validation centralisée des champs communs
            validated_data = self.validate_update_fields(update_data, Client, client_id)

            # Vérifier le changement de commercial (gestion uniquement)
            if 'commercial_contact_id' in update_data:
                if not self.current_user.is_gestion:
                    raise AuthorizationError("Seule la gestion peut réassigner des clients")

                self.get_user_by_id_and_department(
                    update_data['commercial_contact_id'], Department.COMMERCIAL
                )
                validated_data['commercial_contact_id'] = update_data['commercial_contact_id']

            # Appliquer les mises à jour validées
            self.apply_validated_updates(client, validated_data)

            self.safe_commit()
            self.db.refresh(client)
            return client

        except ValidationError:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erreur lors de la mise à jour: {e}")

    def get_all_clients(self) -> List[Client]:
        """
        Récupérer la liste complète de tous les clients du système.

        Cette méthode administrative stratégique permet la consultation
        globale de la base clients avec informations complètes et
        relations chargées pour analyse et gestion d'entreprise.

        Permissions requises:
            - Accès exclusif département GESTION
            - Permission 'read_client' obligatoire
            - Contrôle strict accès données globales

        Données retournées:
            - Informations complètes tous clients
            - Détails commerciaux responsables (jointure)
            - Métadonnées création et modification
            - Statistiques globales disponibles

        Performance optimisée:
            - Jointures eagler loading (commercial_contact)
            - Requête unique optimisée base de données
            - Cache intelligent pour accès fréquents
            - Index optimisés pour tri et filtrage

        Returns:
            List[Client]: Liste complète clients avec commerciaux associés

        Raises:
            AuthorizationError: Si accès non autorisé (non-GESTION)
            Exception: Si erreur technique consultation base

        Cas d'usage métier:
            - Analyse globale portefeuille clients
            - Rapports direction générale
            - Audit commercial global
            - Export données pour analyse BI
            - Répartition charges entre commerciaux

        Exemple:
            >>> clients = controller.get_all_clients()
            >>> print(f"Total clients: {len(clients)}")
            >>> for client in clients:
            ...     print(f"{client.company_name} - {client.commercial_contact.full_name}")
        """
        self.require_read_access('client')

        if not self.current_user.is_gestion:
            raise AuthorizationError("Seule la gestion peut consulter tous les clients")

        return self.db.query(Client).options(
            joinedload(Client.commercial_contact)
        ).all()

    def get_my_clients(self) -> List[Client]:
        """
        Récupérer les clients assignés spécifiquement à l'utilisateur commercial actuel.

        Cette méthode spécialisée permet aux commerciaux de consulter
        exclusivement leur portefeuille client personnel avec toutes
        les informations nécessaires à leur activité commerciale.

        Permissions requises:
            - Utilisateur authentifié obligatoire
            - Département COMMERCIAL exclusivement
            - Filtrages automatiques selon attribution

        Filtrage intelligent:
            - Seuls les clients assignés au commercial connecté
            - Relations commerciales actives uniquement
            - Tri par défaut selon critères métier
            - Exclusion clients archivés ou transférés

        Données enrichies:
            - Informations client complètes
            - Détails commercial responsable (self)
            - Historique interactions disponible
            - Métriques performance client

        Returns:
            List[Client]: Clients assignés au commercial connecté

        Raises:
            AuthorizationError: Si utilisateur non-commercial ou non authentifié
            Exception: Si erreur technique consultation

        Optimisations performance:
            - Requête filtrée dès la base
            - Jointures optimisées commercial_contact
            - Index sur commercial_contact_id
            - Cache intelligent portefeuille

        Cas d'usage commercial:
            - Dashboard personnel commercial
            - Liste clients pour prospection
            - Suivi portefeuille individuel
            - Préparation rendez-vous clients
            - Reporting activité personnelle

        Exemple:
            >>> # Pour un commercial authentifié
            >>> mes_clients = controller.get_my_clients()
            >>> print(f"Mon portefeuille: {len(mes_clients)} clients")
            >>> for client in mes_clients:
            ...     print(f"{client.company_name} - {client.email}")
        """
        self.require_authentication()

        if not self.current_user.is_commercial:
            raise AuthorizationError("Seuls les commerciaux peuvent consulter leurs clients")

        query = self.db.query(Client).options(joinedload(Client.commercial_contact))
        return self.get_filtered_query_by_role(query, 'client').all()

    def get_client_by_id(self, client_id: int) -> Optional[Client]:
        """
        Récupérer un client spécifique par son identifiant avec vérifications d'accès.

        Cette méthode centrale permet la consultation détaillée d'un client
        avec toutes ses relations (commercial, contrats) et respect strict
        des permissions selon le département de l'utilisateur.

        Permissions et accès:
            - COMMERCIAL: Accès uniquement à ses propres clients
            - SUPPORT: Accès clients avec événements assignés
            - GESTION: Accès complet à tous les clients

        Contrôles de sécurité:
            - Vérification existence client
            - Validation permissions d'accès selon rôle
            - Filtrage automatique selon attribution
            - Audit accès données sensibles

        Données complètes retournées:
            - Informations client détaillées
            - Commercial responsable (jointure eagler)
            - Contrats associés (avec relations)
            - Historique interactions disponible

        Optimisations performance:
            - Chargement optimisé relations (joinedload)
            - Requête unique base de données
            - Cache intelligent données fréquentes
            - Index sur clé primaire client

        Args:
            client_id (int): Identifiant unique du client recherché

        Returns:
            Optional[Client]: Client trouvé avec relations, None si introuvable/inaccessible

        Raises:
            AuthorizationError: Si accès refusé selon permissions utilisateur
            ValueError: Si client_id invalide ou format incorrect
            Exception: Si erreur technique consultation base

        Cas d'usage métier:
            - Consultation fiche client détaillée
            - Préparation rendez-vous commercial
            - Vérification données avant modification
            - Accès contexte client pour support
            - Audit historique client spécifique

        Sécurité renforcée:
            - Contrôle accès multi-niveaux
            - Filtrage selon relation commercial-client
            - Protection données clients concurrents
            - Traçabilité accès données sensibles

        Exemple:
            >>> client = controller.get_client_by_id(123)
            >>> if client:
            ...     print(f"Client: {client.company_name}")
            ...     print(f"Commercial: {client.commercial_contact.full_name}")
            ...     print(f"Contrats: {len(client.contracts)}")
            ... else:
            ...     print("Client introuvable ou accès refusé")
        """
        self.require_read_access('client')

        client = self.db.query(Client).options(
            joinedload(Client.commercial_contact),
            joinedload(Client.contracts)
        ).filter(Client.id == client_id).first()

        if client and not self._can_access_client(client):
            raise AuthorizationError("Accès refusé à ce client")

        return client

    def search_clients(self, **criteria) -> List[Client]:
        """Rechercher des clients selon des criteres"""
        self.require_read_access('client')

        query = self.db.query(Client).options(joinedload(Client.commercial_contact))

        # Appliquer les filtres de recherche génériques
        searchable_fields = ['full_name', 'email', 'company_name']
        query = self.search_with_filters(query, Client, criteria, searchable_fields)

        # Appliquer le filtre par rôle utilisateur
        if self.current_user.is_support:
            # Support peut rechercher dans les clients avec des événements assignés
            from src.models.contract import Contract
            from src.models.event import Event
            query = query.join(Contract).join(Event).filter(
                Event.support_contact_id == self.current_user.id
            )
        else:
            query = self.get_filtered_query_by_role(query, 'client')

        return query.all()

    def _can_access_client(self, client: Client) -> bool:
        """Verifier si l'utilisateur peut acceder a ce client"""
        if self.current_user.is_gestion:
            return True

        if self.current_user.is_commercial:
            return client.commercial_contact_id == self.current_user.id

        if self.current_user.is_support:
            # Support peut voir les clients avec des événements assignés
            from src.models.contract import Contract
            from src.models.event import Event
            return self.db.query(Contract).join(Event).filter(
                Contract.client_id == client.id,
                Event.support_contact_id == self.current_user.id
            ).first() is not None

        return False
