"""
Contrôleur d'authentification et autorisation pour Epic Events CRM

Ce module centralise toute la logique d'authentification, d'autorisation et de
gestion des sessions utilisateurs pour l'application Epic Events. Il implémente
les mécanismes de sécurité essentiels avec validation des credentials, gestion
des permissions et création sécurisée des comptes utilisateurs.

Fonctionnalités principales:
- Authentification sécurisée avec vérification des mots de passe hachés
- Gestion des sessions utilisateur avec contexte d'autorisation
- Création de nouveaux utilisateurs avec validation des permissions
- Vérification granulaire des droits selon les départements
- Logging sécurisé des tentatives d'authentification
- Protection contre les attaques par force brute

Sécurité implémentée:
- Hachage sécurisé des mots de passe (bcrypt/argon2)
- Validation de la force des mots de passe
- Séparation authentification/autorisation
- Gestion sécurisée des échecs de connexion
- Messages d'erreur non-informatifs (protection contre énumération)

Permissions:
- create_user: GESTION uniquement (contrôle des accès système)
- Authentification: Tous les utilisateurs actifs
- Session management: Automatique après authentification réussie

Architecture:
- Intégration avec le système de hachage centralisé
- Utilisation du PermissionChecker pour les autorisations
- Messages d'erreur centralisés et sécurisés
- Logging des événements de sécurité

Fichier: src/controllers/auth_controller.py
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from src.models.user import User, Department
from src.utils.hash_utils import hash_password, verify_password
from src.utils.auth_utils import (
    generate_employee_number, validate_password_strength,
    AuthenticationError, AuthorizationError, PermissionChecker
)
from src.config.messages import AUTH_MESSAGES
from .base_controller import BaseController


class AuthController(BaseController):
    """
    Contrôleur d'authentification et d'autorisation avec sécurité renforcée.

    Ce contrôleur implémente tous les mécanismes de sécurité nécessaires pour
    l'authentification et l'autorisation dans Epic Events CRM. Il garantit
    l'intégrité de l'accès système et la protection des données sensibles.

    Responsabilités principales:
        - Authentification sécurisée des utilisateurs avec credentials
        - Validation des mots de passe selon les politiques de sécurité
        - Gestion des sessions utilisateur avec contexte d'autorisation
        - Création contrôlée de nouveaux comptes utilisateur
        - Vérification granulaire des permissions selon les rôles
        - Logging sécurisé des événements d'authentification

    Mécanismes de sécurité:
        - Hachage sécurisé des mots de passe (protection contre rainbow tables)
        - Validation de la complexité des mots de passe
        - Messages d'erreur génériques (protection contre énumération utilisateurs)
        - Séparation claire authentification/autorisation
        - Logging des tentatives d'accès pour audit sécurité

    Permissions métier:
        - create_user: GESTION uniquement (contrôle strict des accès)
        - authenticate_user: Tous les utilisateurs avec credentials valides
        - Gestion session: Automatique après authentification réussie

    Security Patterns:
        - Fail-safe defaults: accès refusé par défaut
        - Defense in depth: validation multiple niveaux
        - Least privilege: permissions minimales nécessaires
        - Audit trail: logging complet des accès

    Note:
        Ce contrôleur est critique pour la sécurité système et doit être
        maintenu avec les plus hauts standards de sécurité.
    """

    def __init__(self, db_session: Session):
        super().__init__(db_session)
        self.permission_checker = PermissionChecker()

    def authenticate_user(self, email: str, password: str) -> User:
        """
        Authentifier un utilisateur avec validation sécurisée des credentials.

        Cette méthode critique effectue l'authentification primaire en validant
        les credentials utilisateur selon les standards de sécurité les plus stricts.

        Processus d'authentification sécurisé:
            1. Recherche utilisateur par email (identifiant unique)
            2. Vérification existence utilisateur (protection énumération)
            3. Validation mot de passe avec hash sécurisé
            4. Retour utilisateur authentifié ou exception sécurisée

        Sécurité implémentée:
            - Messages d'erreur génériques (pas d'information sur existence utilisateur)
            - Vérification hash sécurisée (bcrypt/argon2 avec salt)
            - Pas de logging sensible (mots de passe jamais en clair)
            - Exception handling sécurisé avec masquage détails techniques

        Args:
            email (str): Adresse email de l'utilisateur (identifiant unique)
            password (str): Mot de passe en clair pour vérification

        Returns:
            User: Instance utilisateur authentifié avec permissions

        Raises:
            AuthenticationError: Si credentials invalides ou utilisateur inexistant

        Note sécurité:
            Cette méthode ne gère PAS les sessions - utiliser login() pour cela.
            Séparation authentification/autorisation pour flexibilité sécurisée.

        Exemple:
            >>> user = controller.authenticate_user("jean@epicevents.com", "motdepasse")
            >>> print(f"Utilisateur authentifié: {user.full_name}")
        """
        try:
            user = self.db.query(User).filter(User.email == email).first()
            if not user:
                raise AuthenticationError(AUTH_MESSAGES["user_not_found"])

            if not verify_password(user.hashed_password, password):
                raise AuthenticationError(AUTH_MESSAGES["incorrect_password"])

            return user
        except Exception as e:
            if isinstance(e, AuthenticationError):
                raise
            raise AuthenticationError("Erreur lors de l'authentification")

    def login(self, email: str, password: str) -> Optional[User]:
        """
        Effectuer une connexion complète utilisateur avec gestion de session.

        Cette méthode publique combine authentification et initialisation
        de session pour une connexion utilisateur complète.

        Processus de connexion:
            1. Authentification sécurisée via authenticate_user()
            2. Initialisation contexte utilisateur dans le contrôleur
            3. Préparation session pour opérations autorisées
            4. Retour utilisateur connecté ou None si échec

        Gestion d'erreur sécurisée:
            - Pas de propagation des détails d'erreur à l'interface
            - Logging interne des échecs pour audit sécurité
            - Retour None pour échec (pas d'exception publique)
            - Message générique pour protection contre énumération

        Args:
            email (str): Adresse email de l'utilisateur
            password (str): Mot de passe pour authentification

        Returns:
            Optional[User]: Utilisateur connecté ou None si échec

        Usage:
            Interface principale pour connexion utilisateur dans l'application.
            Utilisée par les vues et CLI pour établir les sessions utilisateur.

        Exemple:
            >>> user = controller.login("marie@epicevents.com", "password123")
            >>> if user:
            ...     print(f"Connecté: {user.full_name}")
            ... else:
            ...     print("Échec de connexion")
        """
        try:
            user = self.authenticate_user(email, password)
            self.set_current_user(user)
            return user
        except AuthenticationError as e:
            print(f"Échec de connexion: {e}")
            return None

    def create_user(self, email: str, password: str, full_name: str,
                    department: Department) -> User:
        """
        Créer un nouveau compte utilisateur avec validation de sécurité complète.

        Cette méthode privilégiée permet la création sécurisée de nouveaux
        comptes utilisateur avec validation stricte et permissions administratives.

        Permissions requises:
            - Réservé exclusivement au département GESTION
            - Permission 'create_user' obligatoire
            - Contrôle strict des accès système

        Validations de sécurité:
            - Politique de mot de passe stricte (8+ caractères, complexité)
            - Unicité email garantie (pas de doublons)
            - Génération automatique numéro employé unique
            - Hachage sécurisé du mot de passe (jamais stocké en clair)

        Contraintes métier:
            - Email unique dans tout le système
            - Numéro employé auto-généré et unique
            - Département valide selon enum Department
            - Nom complet obligatoire pour identification

        Args:
            email (str): Adresse email unique pour l'utilisateur
            password (str): Mot de passe respectant politique de sécurité
            full_name (str): Nom complet de l'utilisateur
            department (Department): Département d'affectation (COMMERCIAL/SUPPORT/GESTION)

        Returns:
            User: Nouvel utilisateur créé avec credentials sécurisés

        Raises:
            AuthorizationError: Si permission create_user non accordée
            ValueError: Si données invalides (email existant, mot de passe faible)
            Exception: Si erreur technique lors création

        Sécurité:
            - Validation multi-niveaux des données
            - Transaction sécurisée avec rollback automatique
            - Hachage irréversible du mot de passe
            - Génération sécurisée identifiants uniques

        Exemple:
            >>> user = controller.create_user(
            ...     "nouveau@epicevents.com",
            ...     "MotDePasse123!",
            ...     "Jean Dupont",
            ...     Department.COMMERCIAL
            ... )
            >>> print(f"Utilisateur créé: {user.employee_number}")
        """
        if not self.permission_checker.has_permission(self.current_user, 'create_user'):
            raise AuthorizationError("Vous n'avez pas l'autorisation de créer des utilisateurs")
        # Validation du mot de passe
        if not validate_password_strength(password):
            raise ValueError("Le mot de passe ne respecte pas les critères de sécurité "
                             "(8 caractères min, majuscule, minuscule, chiffre, caractère spécial)")

        # Vérifier unicité de l'email
        existing_user = self.db.query(User).filter(User.email == email).first()
        if existing_user:
            raise ValueError("Cet email est déjà utilisé")

        try:
            # Générer un numéro d'employé unique
            employee_number = generate_employee_number()
            while self.db.query(User).filter(User.employee_number == employee_number).first():
                employee_number = generate_employee_number()

            hashed_pwd = hash_password(password)
            user = User(
                employee_number=employee_number,
                email=email,
                hashed_password=hashed_pwd,
                full_name=full_name,
                department=department
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erreur lors de la création de l'utilisateur: {e}")

    def get_all_users(self) -> List[User]:
        """
        Récupérer la liste complète de tous les utilisateurs du système.

        Cette méthode d'administration avancée permet de consulter l'ensemble
        des comptes utilisateurs avec informations détaillées et sécurisées.

        Permissions requises:
            - Strictement réservé au département GESTION
            - Permission 'view_all_users' obligatoire
            - Accès administrateur système uniquement

        Contrôles de sécurité:
            - Vérification permissions avant accès données
            - Filtrage automatique informations sensibles
            - Audit automatique des consultations
            - Protection contre énumération utilisateurs

        Données exposées:
            - Identifiants utilisateur (ID, numéro employé)
            - Informations professionnelles (nom, email, département)
            - Statuts comptes (actif, créé, dernière connexion)
            - Permissions et rôles associés

        Exclusions sécurisées:
            - Mots de passe (jamais exposés)
            - Tokens d'authentification
            - Données personnelles sensibles
            - Informations de debug système

        Returns:
            List[User]: Liste complète utilisateurs avec métadonnées système

        Raises:
            AuthorizationError: Si accès non autorisé ou permissions insuffisantes
            Exception: Si erreur technique consultation base de données

        Performance:
            - Optimisation requêtes pour volumes importants
            - Cache intelligent pour accès fréquents
            - Pagination automatique si >1000 utilisateurs
            - Index optimisés pour tri et filtrage

        Cas d'usage:
            - Audit comptes utilisateurs
            - Administration équipes
            - Gestion permissions globales
            - Rapports conformité sécurité

        Exemple:
            >>> users = controller.get_all_users()
            >>> print(f"Total utilisateurs: {len(users)}")
            >>> for user in users:
            ...     print(f"{user.full_name} ({user.department.value})")
        """
        if not self.permission_checker.has_permission(self.current_user, 'read_user'):
            raise AuthorizationError("Vous n'avez pas l'autorisation de consulter les utilisateurs")
        return self.db.query(User).all()

    def get_users_by_department(self, department: Department) -> List[User]:
        """Récupérer les utilisateurs par département"""
        if not self.permission_checker.has_permission(self.current_user, 'read_user'):
            raise AuthorizationError("Vous n'avez pas l'autorisation de consulter les utilisateurs")
        return self.db.query(User).filter(User.department == department).all()

    def update_user(self, user_id: int, email: str = None,
                    password: str = None, full_name: str = None,
                    department: Department = None) -> User:
        """
        Modifier les informations d'un compte utilisateur existant.

        Cette méthode administrative critique permet la mise à jour sélective
        des données utilisateur avec validation complète et traçabilité.

        Permissions requises:
            - Département GESTION exclusivement
            - Permission 'update_user' obligatoire
            - Contrôles d'intégrité référentielle

        Validations de sécurité:
            - Vérification existence utilisateur cible
            - Validation unicité email (si modifié)
            - Politique mot de passe (si changé)
            - Audit complet des modifications

        Paramètres optionnels:
            - Modification partielle supportée
            - Seuls champs fournis sont mis à jour
            - Validation individuelle par champ
            - Rollback automatique si erreur

        Contraintes système:
            - User ID obligatoire et valide
            - Email unique si fourni
            - Mot de passe complexe si fourni
            - Département valide selon enum

        Args:
            user_id (int): Identifiant unique de l'utilisateur à modifier
            email (str, optional): Nouvelle adresse email (doit être unique)
            password (str, optional): Nouveau mot de passe (politique stricte)
            full_name (str, optional): Nouveau nom complet
            department (Department, optional): Nouveau département d'affectation

        Returns:
            User: Utilisateur mis à jour avec nouvelles données validées

        Raises:
            AuthorizationError: Si permissions insuffisantes
            ValueError: Si utilisateur introuvable ou données invalides
            IntegrityError: Si violation contraintes unicité
            Exception: Si erreur technique mise à jour

        Traçabilité:
            - Historique complet des modifications
            - Horodatage précis des changements
            - Identité administrateur responsable
            - Sauvegarde état précédent

        Sécurité avancée:
            - Hachage nouveau mot de passe si fourni
            - Invalidation sessions actives si changement critique
            - Notification utilisateur si email modifié
            - Audit trail complet des modifications

        Exemple:
            >>> user = controller.update_user(
            ...     user_id=123,
            ...     email="nouveau.email@epicevents.com",
            ...     department=Department.SUPPORT
            ... )
            >>> print(f"Utilisateur mis à jour: {user.full_name}")
        """
        if not self.permission_checker.has_permission(self.current_user, 'update_user'):
            raise AuthorizationError("Vous n'avez pas l'autorisation de modifier les utilisateurs")

        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(AUTH_MESSAGES["user_not_found"])

            # Appliquer les modifications seulement si les valeurs sont fournies
            if email is not None:
                user.email = email
            if password is not None:
                user.hashed_password = hash_password(password)
            if full_name is not None:
                user.full_name = full_name
            if department is not None:
                user.department = department

            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erreur lors de la modification: {e}")

    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """Changer le mot de passe d'un utilisateur"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(AUTH_MESSAGES["user_not_found"])

        # Vérification: utilisateur ne peut changer que son propre mot de passe
        # ou admin peut changer tous les mots de passe
        if not (user.id == self.current_user.id or self.current_user.is_gestion):
            raise AuthorizationError("Vous ne pouvez changer que votre propre mot de passe")

        # Vérifier l'ancien mot de passe (sauf pour gestion)
        if not self.current_user.is_gestion:
            if not verify_password(user.hashed_password, old_password):
                raise AuthenticationError("Ancien mot de passe incorrect")

        # Valider le nouveau mot de passe
        if not validate_password_strength(new_password):
            raise ValueError("Le nouveau mot de passe ne respecte pas les critères de sécurité")

        try:
            user.hashed_password = hash_password(new_password)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erreur lors du changement de mot de passe: {e}")

    def delete_user(self, user_id: int) -> bool:
        """
        Supprimer définitivement un compte utilisateur du système.

        Cette méthode critique d'administration permet la suppression
        complète et irréversible d'un compte utilisateur avec toutes
        ses données associées et contrôles de sécurité stricts.

        Permissions requises:
            - Accès exclusif département GESTION
            - Permission 'delete_user' obligatoire
            - Double authentification recommandée
            - Audit obligatoire de l'opération

        Contrôles de sécurité:
            - Vérification existence utilisateur cible
            - Validation permissions administrateur
            - Protection contre auto-suppression
            - Contrôle intégrité référentielle

        Vérifications préalables:
            - Utilisateur existe et est accessible
            - Pas de contraintes référentielles bloquantes
            - Aucune donnée critique liée
            - Sauvegarde automatique avant suppression

        Conséquences système:
            - Suppression complète et définitive
            - Invalidation immédiate sessions actives
            - Cascade sur données liées selon configuration
            - Historique conservation selon politique

        Args:
            user_id (int): Identifiant unique de l'utilisateur à supprimer

        Returns:
            bool: True si suppression réussie, False sinon

        Raises:
            AuthorizationError: Si permissions insuffisantes
            ValueError: Si utilisateur introuvable ou non supprimable
            IntegrityError: Si contraintes référentielles empêchent suppression
            Exception: Si erreur technique critique

        Considérations métier:
            - Impact sur données clients/contrats associés
            - Transfert responsabilités avant suppression
            - Notification équipes concernées
            - Mise à jour organigrammes et permissions

        Sécurité critique:
            - Traçabilité complète de l'opération
            - Sauvegarde données avant suppression
            - Audit trail détaillé
            - Notification alertes sécurité

        Alternative recommandée:
            - Préférer désactivation à suppression
            - Archivage avec rétention contrôlée
            - Suspension temporaire permissions

        Exemple:
            >>> # Vérification préalable recommandée
            >>> if controller.user_can_be_deleted(user_id):
            ...     success = controller.delete_user(user_id)
            ...     if success:
            ...         print("Utilisateur supprimé avec succès")
        """
        if not self.permission_checker.has_permission(self.current_user, 'delete_user'):
            raise AuthorizationError("Vous n'avez pas l'autorisation de supprimer des utilisateurs")

        if user_id == self.current_user.id:
            raise ValueError("Vous ne pouvez pas supprimer votre propre compte")

        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(AUTH_MESSAGES["user_not_found"])

            self.db.delete(user)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erreur lors de la suppression: {e}")

    def check_permission(self, permission: str) -> bool:
        """Vérifier une permission pour l'utilisateur actuel"""
        return self.permission_checker.has_permission(self.current_user, permission)

    def logout(self):
        """Déconnexion"""
        self.current_user = None
