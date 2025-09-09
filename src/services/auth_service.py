"""
Service d'authentification et d'autorisation Epic Events CRM

Ce module fournit une couche de service complète pour la gestion de
l'authentification et de l'autorisation dans l'application Epic Events.
Il implémente un système de sécurité robuste basé sur JWT avec contrôle
d'accès granulaire par rôles et permissions.

Architecture de sécurité:
    1. Authentification: Vérification d'identité via email/mot de passe
    2. Autorisation: Contrôle d'accès basé sur les départements utilisateur
    3. Session: Gestion des tokens JWT avec expiration et rotation
    4. Audit: Logging automatique de toutes les tentatives d'accès

Fonctionnalités principales:
    - Login/logout sécurisé avec génération de tokens JWT
    - Vérification des permissions par département et ressource
    - Gestion des sessions utilisateur avec contexte Sentry
    - Protection contre les attaques par force brute
    - Audit trail complet des accès et tentatives

Intégrations:
    - JWT: Tokens sécurisés pour authentification stateless
    - Sentry: Monitoring en temps réel des tentatives d'accès
    - Argon2: Vérification sécurisée des mots de passe
    - Base de données: Requêtes optimisées pour authentification

Sécurité implémentée:
    - Résistance aux attaques timing via vérification constante
    - Tokens JWT avec expiration automatique
    - Logging détaillé pour détection d'intrusions
    - Validation stricte des permissions avant accès ressources

Fichier: src/services/auth_service.py
"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from src.models.user import User
from src.utils.hash_utils import verify_password
from src.utils.jwt_utils import JWTManager
from src.utils.auth_utils import (
    AuthenticationError, AuthorizationError, PermissionChecker
)
from src.config.messages import AUTH_MESSAGES
from src.services.logging_service import SentryLogger


class AuthenticationService:
    """
    Service d'authentification et d'autorisation avec support JWT et audit.

    Cette classe centralise toute la logique d'authentification et d'autorisation
    de l'application Epic Events. Elle fournit une interface cohérente pour
    la vérification d'identité, la gestion des sessions et le contrôle d'accès
    aux ressources métier.

    Responsabilités:
        - Authentification des utilisateurs via credentials
        - Génération et validation des tokens JWT
        - Contrôle d'accès basé sur les permissions départementales
        - Audit automatique des tentatives d'accès
        - Gestion du contexte utilisateur pour monitoring

    Architecture de sécurité:
        - Authentification: Vérification email/password avec Argon2
        - Autorisation: Permissions granulaires par département
        - Sessions: JWT avec expiration et rotation automatique
        - Audit: Logging Sentry de tous les événements sécuritaires

    Patterns implémentés:
        - Service Layer: Logique métier centralisée
        - Facade: Interface simplifiée pour authentification complexe
        - Strategy: Différentes stratégies d'autorisation selon contexte
        - Observer: Logging automatique des événements critiques

    Attributes:
        db: Session de base de données pour requêtes utilisateur
        jwt_manager: Gestionnaire des tokens JWT
        permission_checker: Vérificateur de permissions métier
        sentry_logger: Service de logging et monitoring
    """

    def __init__(self, db_session: Session):
        """
        Initialiser le service d'authentification.

        Args:
            db_session: Session SQLAlchemy pour accès base de données
        """
        self.db = db_session
        self.jwt_manager = JWTManager()
        self.permission_checker = PermissionChecker()
        self.sentry_logger = SentryLogger()

    def login(self, email: str, password: str) -> Optional[User]:
        """
        Authentifier un utilisateur et créer une session sécurisée.

        Cette méthode implémente le processus complet d'authentification
        avec vérification des credentials, génération de token JWT et
        initialisation du contexte de sécurité pour la session.

        Args:
            email: Adresse email de l'utilisateur
            password: Mot de passe en clair à vérifier

        Returns:
            User: Instance de l'utilisateur authentifié

        Raises:
            AuthenticationError: Si les credentials sont invalides

        Sécurité:
            - Vérification en temps constant (résistant aux attaques timing)
            - Logging automatique des tentatives (succès et échecs)
            - Génération de token JWT sécurisé avec claims métier
            - Initialisation du contexte Sentry pour monitoring

        Workflow:
            1. Recherche de l'utilisateur par email
            2. Vérification du mot de passe avec Argon2
            3. Génération du token JWT avec données utilisateur
            4. Sauvegarde du token pour validation future
            5. Configuration du contexte monitoring Sentry
        """
        try:
            # Recherche de l'utilisateur dans la base de données
            user = self.db.query(User).filter(User.email == email).first()
            if not user:
                self.sentry_logger.log_authentication_attempt(email, False)
                raise AuthenticationError(AUTH_MESSAGES["user_not_found"])

            # Vérification sécurisée du mot de passe avec Argon2
            # Temps constant pour éviter les attaques timing
            if not verify_password(user.hashed_password, password):
                self.sentry_logger.log_authentication_attempt(email, False)
                raise AuthenticationError(AUTH_MESSAGES["incorrect_password"])

            # Génération du token JWT avec claims utilisateur métier
            token = self.jwt_manager.generate_token(
                user_id=user.id,
                email=user.email,
                department=user.department.value,
                employee_number=user.employee_number
            )

            # Sauvegarde du token pour validation des requêtes futures
            if self.jwt_manager.save_token(token):
                # Logging du succès et initialisation contexte monitoring
                self.sentry_logger.log_authentication_attempt(email, True)
                self.sentry_logger.set_user_context(user)
                return user
            else:
                raise Exception(AUTH_MESSAGES["token_save_error"])

        except AuthenticationError:
            # Re-lever les erreurs d'authentification sans transformation
            raise
        except Exception as e:
            # Logger les erreurs techniques et les transformer en erreur métier
            SentryLogger().log_exception(e, {"context": "user_login", "email": email})
            raise AuthenticationError(AUTH_MESSAGES["login_error"].format(error=e))

    def logout(self) -> bool:
        """
        Déconnecter l'utilisateur et nettoyer la session.

        Cette méthode termine proprement la session utilisateur en
        supprimant le token JWT et en nettoyant le contexte de sécurité.

        Returns:
            bool: True si la déconnexion s'est bien déroulée

        Sécurité:
            - Invalidation du token JWT côté serveur
            - Nettoyage du contexte utilisateur Sentry
            - Logging de la déconnexion pour audit

        Note:
            Cette méthode ne lève pas d'exception même si l'utilisateur
            n'était pas connecté, permettant une déconnexion "safe".
        """
        try:
            # Nettoyage du contexte utilisateur Sentry pour arrêter le tracking
            self.sentry_logger.clear_user_context()

            # Invalidation du token JWT côté serveur
            return self.jwt_manager.logout()

        except Exception as e:
            # Logger l'erreur mais ne pas échouer la déconnexion
            self.sentry_logger.log_exception(e, {"action": "logout"})
            return False

    def get_current_user(self) -> Optional[User]:
        """
        Récupérer l'utilisateur actuellement authentifié.

        Cette méthode extrait les informations utilisateur du token JWT
        actuel et récupère l'instance complète depuis la base de données.

        Returns:
            User: Instance de l'utilisateur connecté, None si non connecté

        Performance:
            - Utilise le cache JWT pour éviter les requêtes répétées
            - Requête base de données uniquement si token valide
            - Gestion optimisée des sessions expirées
        """
        # Extraction des données depuis le token JWT
        user_data = self.jwt_manager.get_current_user_data()
        if not user_data:
            return None

        # Récupération de l'instance utilisateur complète depuis la base
        user = self.db.query(User).filter(User.id == user_data['user_id']).first()
        return user

    def is_authenticated(self) -> bool:
        """
        Vérifier si un utilisateur est actuellement authentifié.

        Cette méthode vérifie rapidement l'état d'authentification sans
        charger les données utilisateur complètes, optimisée pour les
        contrôles d'accès fréquents.

        Returns:
            bool: True si utilisateur authentifié avec token valide
        """
        return self.jwt_manager.is_authenticated()

    def require_authentication(self) -> User:
        """
        Exiger une authentification valide ou lever une exception.

        Cette méthode est utilisée dans les contrôleurs pour s'assurer
        qu'un utilisateur est authentifié avant d'autoriser l'accès à
        une ressource protégée.

        Returns:
            User: Instance de l'utilisateur authentifié

        Raises:
            AuthenticationError: Si aucun utilisateur n'est connecté

        Utilisation:
            Placée en début de méthodes de contrôleur nécessitant
            une authentification, elle garantit qu'un utilisateur
            valide est disponible pour la suite du traitement.
        """
        current_user = self.get_current_user()
        if not current_user:
            raise AuthenticationError(AUTH_MESSAGES["authentication_required"])
        return current_user

    def check_permission(self, permission: str) -> bool:
        """
        Vérifier si l'utilisateur actuel possède une permission donnée.

        Cette méthode vérifie les permissions métier sans lever d'exception,
        permettant une logique conditionnelle dans les contrôleurs.

        Args:
            permission: Nom de la permission à vérifier (ex: "client.create")

        Returns:
            bool: True si l'utilisateur possède la permission
        """
        current_user = self.get_current_user()
        if not current_user:
            return False
        return self.permission_checker.has_permission(current_user, permission)

    def require_permission(self, permission: str) -> User:
        """
        Exiger une permission spécifique ou lever une exception.

        Cette méthode combine vérification d'authentification et d'autorisation
        pour protéger les opérations métier critiques nécessitant des
        permissions particulières.

        Args:
            permission: Nom de la permission requise

        Returns:
            User: Instance de l'utilisateur autorisé

        Raises:
            AuthenticationError: Si l'utilisateur n'est pas connecté
            AuthorizationError: Si l'utilisateur n'a pas la permission

        Utilisation:
            Protège les opérations sensibles comme la création d'utilisateurs
            (réservée à GESTION) ou la signature de contrats.
        """
        current_user = self.require_authentication()
        if not self.permission_checker.has_permission(current_user, permission):
            raise AuthorizationError(AUTH_MESSAGES["permission_required"].format(permission=permission))
        return current_user

    def can_access_resource(self, resource_type: str, resource_owner_id: int = None,
                            assigned_user_id: int = None) -> bool:
        """
        Vérifier l'accès à une ressource spécifique selon les règles métier.

        Cette méthode implémente les règles d'accès granulaires aux ressources
        métier, prenant en compte la propriété et l'assignation des ressources.

        Args:
            resource_type: Type de ressource ("client", "contract", "event")
            resource_owner_id: ID du propriétaire de la ressource (commercial)
            assigned_user_id: ID de l'utilisateur assigné (support pour événements)

        Returns:
            bool: True si l'accès est autorisé selon les règles métier

        Règles d'accès:
            - GESTION: Accès complet à toutes les ressources
            - COMMERCIAL: Accès à ses propres clients et contrats
            - SUPPORT: Accès aux événements qui leur sont assignés
        """
        current_user = self.get_current_user()
        if not current_user:
            return False

        return self.permission_checker.can_access_resource(
            current_user, resource_type, resource_owner_id, assigned_user_id
        )

    def get_token_info(self) -> Optional[Dict[str, Any]]:
        """
        Récupérer les informations complètes du token JWT actuel.

        Cette méthode expose les claims du token JWT pour debugging
        et audit, sans révéler d'informations sensibles.

        Returns:
            Dict: Informations du token (user_id, email, department, etc.)
                 None si aucun token valide

        Utilisation:
            - Debugging des problèmes d'authentification
            - Audit des sessions utilisateur
            - Interface d'administration système
        """
        return self.jwt_manager.get_current_user_data()
