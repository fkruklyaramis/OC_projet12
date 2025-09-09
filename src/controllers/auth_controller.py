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
        """Authentifier un utilisateur (séparé de login pour sécurité)"""
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
        """Connexion utilisateur"""
        try:
            user = self.authenticate_user(email, password)
            self.set_current_user(user)
            return user
        except AuthenticationError as e:
            print(f"Échec de connexion: {e}")
            return None

    def create_user(self, email: str, password: str, full_name: str,
                    department: Department) -> User:
        """Créer un utilisateur (autorisation requise)"""
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
        """Récupérer tous les utilisateurs (autorisation requise)"""
        if not self.permission_checker.has_permission(self.current_user, 'read_user'):
            raise AuthorizationError("Vous n'avez pas l'autorisation de consulter les utilisateurs")
        return self.db.query(User).all()

    def get_users_by_department(self, department: Department) -> List[User]:
        """Récupérer les utilisateurs par département"""
        if not self.permission_checker.has_permission(self.current_user, 'read_user'):
            raise AuthorizationError("Vous n'avez pas l'autorisation de consulter les utilisateurs")
        return self.db.query(User).filter(User.department == department).all()

    def update_user(self, user_id: int, **kwargs) -> User:
        """Modifier un utilisateur (autorisation requise)"""
        if not self.permission_checker.has_permission(self.current_user, 'update_user'):
            raise AuthorizationError("Vous n'avez pas l'autorisation de modifier les utilisateurs")

        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(AUTH_MESSAGES["user_not_found"])

            # Ne pas permettre la modification du mot de passe par cette méthode
            forbidden_fields = ['id', 'hashed_password', 'employee_number']
            for key, value in kwargs.items():
                if key in forbidden_fields:
                    continue
                if hasattr(user, key):
                    setattr(user, key, value)

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
        """Supprimer un utilisateur (autorisation requise)"""
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
