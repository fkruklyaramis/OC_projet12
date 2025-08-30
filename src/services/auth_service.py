from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from src.models.user import User
from src.utils.hash_utils import verify_password
from src.utils.jwt_utils import JWTManager
from src.utils.auth_utils import (
    AuthenticationError, AuthorizationError, PermissionChecker
)
from src.config.messages import AUTH_MESSAGES


class AuthenticationService:
    """Service d'authentification avec support JWT"""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.jwt_manager = JWTManager()
        self.permission_checker = PermissionChecker()

    def login(self, email: str, password: str) -> Optional[User]:
        """Connexion utilisateur avec génération de token JWT"""
        try:
            # Authentifier l'utilisateur
            user = self.db.query(User).filter(User.email == email).first()
            if not user:
                raise AuthenticationError(AUTH_MESSAGES["user_not_found"])

            if not verify_password(user.hashed_password, password):
                raise AuthenticationError(AUTH_MESSAGES["incorrect_password"])

            # Générer et sauvegarder le token JWT
            token = self.jwt_manager.generate_token(
                user_id=user.id,
                email=user.email,
                department=user.department.value,
                employee_number=user.employee_number
            )

            if self.jwt_manager.save_token(token):
                return user
            else:
                raise Exception(AUTH_MESSAGES["token_save_error"])

        except AuthenticationError:
            raise
        except Exception as e:
            raise AuthenticationError(AUTH_MESSAGES["login_error"].format(error=e))

    def logout(self) -> bool:
        """Déconnexion utilisateur - suppression du token"""
        return self.jwt_manager.clear_token()

    def get_current_user(self) -> Optional[User]:
        """Récupérer l'utilisateur actuellement connecté"""
        user_data = self.jwt_manager.get_current_user_data()
        if not user_data:
            return None

        # Récupérer l'utilisateur depuis la base de données
        user = self.db.query(User).filter(User.id == user_data['user_id']).first()
        return user

    def is_authenticated(self) -> bool:
        """Vérifier si un utilisateur est authentifié"""
        return self.jwt_manager.is_authenticated()

    def require_authentication(self) -> User:
        """Exiger une authentification - lancer exception si non connecté"""
        current_user = self.get_current_user()
        if not current_user:
            raise AuthenticationError(AUTH_MESSAGES["authentication_required"])
        return current_user

    def check_permission(self, permission: str) -> bool:
        """Vérifier une permission pour l'utilisateur actuel"""
        current_user = self.get_current_user()
        if not current_user:
            return False
        return self.permission_checker.has_permission(current_user, permission)

    def require_permission(self, permission: str) -> User:
        """Exiger une permission - lancer exception si non autorisé"""
        current_user = self.require_authentication()
        if not self.permission_checker.has_permission(current_user, permission):
            raise AuthorizationError(AUTH_MESSAGES["permission_required"].format(permission=permission))
        return current_user

    def can_access_resource(self, resource_type: str, resource_owner_id: int = None,
                            assigned_user_id: int = None) -> bool:
        """Vérifier l'accès à une ressource spécifique"""
        current_user = self.get_current_user()
        if not current_user:
            return False

        return self.permission_checker.can_access_resource(
            current_user, resource_type, resource_owner_id, assigned_user_id
        )

    def get_token_info(self) -> Optional[Dict[str, Any]]:
        """Récupérer les informations du token actuel"""
        return self.jwt_manager.get_current_user_data()
