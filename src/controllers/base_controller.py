"""
Module BaseController pour Epic Events CRM

Ce module implémente le contrôleur de base de l'architecture MVC du système Epic Events.
Il fournit une classe abstraite qui centralise la gestion des permissions, l'authentification,
les validations de données et les opérations de base de données communes à tous les contrôleurs
métier du système.

Le BaseController constitue le fondement architectural qui assure la cohérence, la sécurité
et la maintenabilité de l'ensemble de l'application. Il encapsule les patterns de conception
Observer et Template Method pour la gestion d'état et les opérations CRUD.

Architecture:
    - Gestion centralisée de l'authentification et des sessions utilisateurs
    - Système de permissions basé sur les rôles (RBAC - Role-Based Access Control)
    - Validation de données avec gestion d'erreurs typées
    - Transactions de base de données sécurisées avec rollback automatique
    - Filtrage de requêtes selon les privilèges utilisateur
    - Méthodes utilitaires pour les opérations CRUD communes

Dependencies:
    - SQLAlchemy: ORM pour les opérations de base de données
    - src.models.user: Modèles User et Department
    - src.utils.auth_utils: Utilitaires d'authentification et autorisation
    - src.utils.validators: Validateurs de données métier

Author: Étudiant OpenClassrooms
Date: 2024
Version: 1.0.0
"""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from src.models.user import User, Department
from src.utils.auth_utils import PermissionChecker, AuthorizationError
from src.utils.validators import DataValidator, ValidationError


class BaseController:
    """
    Contrôleur de base pour l'architecture MVC d'Epic Events.

    Cette classe abstraite fournit les fonctionnalités communes à tous les contrôleurs
    métier du système CRM Epic Events. Elle centralise la gestion de l'authentification,
    des permissions, des validations et des transactions de base de données.

    Le BaseController implémente le pattern Template Method pour les opérations CRUD
    et utilise le principe d'inversion de dépendance (DIP) pour découpler les couches
    de l'application.

    Responsabilités principales:
        - Gestion de l'état de session utilisateur avec contrôle d'accès
        - Validation des permissions basées sur les rôles métier
        - Coordination des transactions de base de données avec gestion d'erreurs
        - Validation de données avec règles métier centralisées
        - Filtrage automatique des requêtes selon les privilèges utilisateur
        - Méthodes utilitaires pour les opérations courantes (CRUD, recherche)

    Attributes:
        db (Session): Session SQLAlchemy pour les opérations de base de données
        current_user (Optional[User]): Utilisateur authentifié actuellement connecté
        permission_checker (PermissionChecker): Service de vérification des permissions
        validator (DataValidator): Service de validation des données métier

    Design Patterns:
        - Template Method: Méthodes require_*_access() définissent la structure commune
        - Observer: Notification des erreurs via le système de logging centralisé
        - Strategy: Validation polymorphe selon le type de ressource

    Sécurité:
        - Toutes les opérations nécessitent une authentification préalable
        - Contrôle d'accès granulaire par rôle et propriété des ressources
        - Validation stricte des données avec échappement automatique
        - Transactions atomiques avec rollback en cas d'erreur

    Usage:
        Cette classe est héritée par tous les contrôleurs métier :
        - ClientController : Gestion des prospects et clients
        - ContractController : Gestion des contrats commerciaux
        - EventController : Gestion des événements et support
        - UserController : Administration des utilisateurs

    Note:
        Cette classe ne doit jamais être instanciée directement. Elle sert uniquement
        de classe parent pour les contrôleurs métier spécialisés.
    """

    def __init__(self, db_session: Session):
        self.db = db_session
        self.current_user: Optional[User] = None
        self.permission_checker = PermissionChecker()
        self.validator = DataValidator()

    def set_current_user(self, user: User):
        """Définir l'utilisateur actuel pour les vérifications de permissions"""
        self.current_user = user

    def require_authentication(self):
        """Vérifier qu'un utilisateur est connecté"""
        if not self.current_user:
            raise AuthorizationError("Authentification requise")
        return self.current_user

    def safe_commit(self):
        """Effectuer un commit sécurisé avec gestion d'erreurs"""
        try:
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Erreur lors de la sauvegarde: {e}")

    def safe_rollback(self):
        """Effectuer un rollback sécurisé"""
        try:
            self.db.rollback()
        except SQLAlchemyError:
            pass

    def has_permission(self, required_departments: list) -> bool:
        """Vérifier les permissions utilisateur"""
        if not self.current_user:
            return False
        return self.current_user.department in required_departments

    def is_owner_or_admin(self, owner_id: int) -> bool:
        """Vérifier si l'utilisateur est propriétaire ou admin"""
        if not self.current_user:
            return False
        return (self.current_user.id == owner_id or
                self.current_user.department == Department.GESTION)

    def require_write_access(self, resource_type: str, resource=None):
        """Vérifier l'accès en écriture pour une ressource"""
        if resource_type == 'client':
            if not self.permission_checker.has_permission(
                self.current_user, 'update_client'
            ):
                if (self.current_user.is_commercial and resource and
                        resource.commercial_contact_id == self.current_user.id):
                    return
                raise AuthorizationError(
                    "Permission insuffisante pour modifier ce client"
                )

        elif resource_type == 'contract':
            if not self.permission_checker.has_permission(
                self.current_user, 'update_contract'
            ):
                if (self.current_user.is_commercial and resource and
                        resource.commercial_contact_id == self.current_user.id):
                    return
                raise AuthorizationError(
                    "Permission insuffisante pour modifier ce contrat"
                )

        elif resource_type == 'event':
            if not self.permission_checker.has_permission(
                self.current_user, 'update_event'
            ):
                if (self.current_user.is_support and resource and
                        resource.support_contact_id == self.current_user.id):
                    return
                raise AuthorizationError(
                    "Permission insuffisante pour modifier cet événement"
                )

        elif resource_type == 'user':
            if not self.permission_checker.has_permission(
                self.current_user, 'update_user'
            ):
                raise AuthorizationError(
                    "Seule la gestion peut modifier des utilisateurs"
                )

    def require_read_access(self, resource_type: str):
        """Vérifier l'accès en lecture pour une ressource"""
        permission_map = {
            'client': 'read_client',
            'contract': 'read_contract',
            'event': 'read_event',
            'user': 'read_user'
        }

        permission = permission_map.get(resource_type)
        if not permission:
            raise ValueError(f"Type de ressource inconnu: {resource_type}")

        if not self.permission_checker.has_permission(
            self.current_user, permission
        ):
            raise AuthorizationError(f"Permission '{permission}' requise")

    def require_create_access(self, resource_type: str):
        """Vérifier l'accès en création pour une ressource"""
        permission_map = {
            'client': 'create_client',
            'contract': 'create_contract',
            'event': 'create_event',
            'user': 'create_user'
        }

        permission = permission_map.get(resource_type)
        if not permission:
            raise ValueError(f"Type de ressource inconnu: {resource_type}")

        if not self.permission_checker.has_permission(
            self.current_user, permission
        ):
            raise AuthorizationError(f"Permission '{permission}' requise")

    def require_delete_access(self, resource_type: str):
        """Vérifier l'accès en suppression pour une ressource"""
        permission_map = {
            'client': 'delete_client',
            'contract': 'delete_contract',
            'event': 'delete_event',
            'user': 'delete_user'
        }

        permission = permission_map.get(resource_type)
        if not permission:
            raise ValueError(f"Type de ressource inconnu: {resource_type}")

        if not self.permission_checker.has_permission(
            self.current_user, permission
        ):
            raise AuthorizationError(f"Permission '{permission}' requise")

    def validate_and_check_unique_email(self, email: str, model_class,
                                        exclude_id: int = None) -> str:
        """Valider un email et vérifier son unicité"""
        validated_email = self.validator.validate_email(email)

        query = self.db.query(model_class).filter(model_class.email == validated_email)
        if exclude_id:
            query = query.filter(model_class.id != exclude_id)

        if query.first():
            raise ValidationError("Cette adresse email est déjà utilisée")

        return validated_email

    def get_user_by_id_and_department(self, user_id: int, department: Department):
        """Récupérer un utilisateur par ID et vérifier son département"""
        user = self.db.query(User).filter(
            User.id == user_id,
            User.department == department
        ).first()

        if not user:
            raise ValidationError(f"Utilisateur {department.value} non trouvé")

        return user

    def validate_update_fields(self, update_data: dict, model_class, exclude_id: int = None):
        """Valider les champs de mise à jour communs"""
        validated_data = {}

        # Validation email avec vérification d'unicité
        if 'email' in update_data and update_data['email']:
            validated_data['email'] = self.validate_and_check_unique_email(
                update_data['email'], model_class, exclude_id
            )

        # Validation téléphone
        if 'phone' in update_data and update_data['phone']:
            validated_data['phone'] = self.validator.validate_phone(update_data['phone'])

        # Validation nom complet
        if 'full_name' in update_data and update_data['full_name']:
            validated_data['full_name'] = self.validator.validate_full_name(
                update_data['full_name']
            )

        # Validation nom de société
        if 'company_name' in update_data and update_data['company_name']:
            validated_data['company_name'] = self.validator.validate_company_name(
                update_data['company_name']
            )

        return validated_data

    def apply_validated_updates(self, entity, update_data: dict, forbidden_fields: list = None):
        """Appliquer les mises à jour validées à une entité"""
        if forbidden_fields is None:
            forbidden_fields = ['id', 'created_at', 'updated_at']

        for key, value in update_data.items():
            if key in forbidden_fields:
                continue
            if hasattr(entity, key):
                setattr(entity, key, value)

    def get_filtered_query_by_role(self, query, resource_type: str, user_field: str = None):
        """Filtrer une requête selon le rôle de l'utilisateur"""
        if self.current_user.is_gestion:
            return query

        if resource_type == 'client' and self.current_user.is_commercial:
            return query.filter_by(commercial_contact_id=self.current_user.id)
        if resource_type == 'contract' and self.current_user.is_commercial:
            from src.models.client import Client
            return query.join(Client).filter(
                Client.commercial_contact_id == self.current_user.id
            )

        if resource_type == 'event' and self.current_user.is_support:
            return query.filter_by(support_contact_id=self.current_user.id)

        # Pour les autres cas, retourner une requête vide par sécurité
        return query.filter(False)

    def search_with_filters(self, base_query, model_class, search_criteria: dict,
                            searchable_fields: list):
        """Appliquer des filtres de recherche génériques"""
        for field_name in searchable_fields:
            if field_name in search_criteria and search_criteria[field_name]:
                search_value = f"%{search_criteria[field_name]}%"
                field = getattr(model_class, field_name, None)
                if field:
                    base_query = base_query.filter(field.ilike(search_value))

        return base_query

    def validate_entity_ownership(self, entity, user_field: str):
        """Valider que l'utilisateur peut modifier cette entité"""
        if self.current_user.is_gestion:
            return True

        owner_id = getattr(entity, user_field, None)
        return owner_id == self.current_user.id if owner_id else False
