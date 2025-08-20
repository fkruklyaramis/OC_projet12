import secrets
import string
from src.models.user import User, Department


def generate_employee_number() -> str:
    """Générer un numéro d'employé unique"""
    # Format: EE + 6 chiffres aléatoirement
    digits = ''.join(secrets.choice(string.digits) for _ in range(6))
    return f"EE{digits}"


def validate_password_strength(password: str) -> bool:
    """Valider la force du mot de passe"""
    if len(password) < 8:
        return False

    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

    return has_upper and has_lower and has_digit and has_special


class AuthenticationError(Exception):
    """Exception pour les erreurs d'authentification"""
    pass


class AuthorizationError(Exception):
    """Exception pour les erreurs d'autorisation"""
    pass


class PermissionChecker:
    """Gestionnaire des permissions par département"""

    # Permissions par département
    PERMISSIONS = {
        Department.COMMERCIAL: {
            'create_client': True,
            'read_client': True,
            'update_own_client': True,
            'delete_client': False,
            'create_contract': False,
            'read_contract': True,
            'update_own_contract': True,
            'delete_contract': False,
            'create_event': True,
            'read_event': True,
            'update_event': False,
            'delete_event': False,
            'create_user': False,
            'read_user': False,
            'update_user': False,
            'delete_user': False,
        },
        Department.SUPPORT: {
            'create_client': False,
            'read_client': True,
            'update_own_client': False,
            'delete_client': False,
            'create_contract': False,
            'read_contract': True,
            'update_own_contract': False,
            'delete_contract': False,
            'create_event': False,
            'read_event': True,
            'update_assigned_event': True,
            'delete_event': False,
            'create_user': False,
            'read_user': False,
            'update_user': False,
            'delete_user': False,
        },
        Department.GESTION: {
            'create_client': True,
            'read_client': True,
            'update_client': True,
            'delete_client': True,
            'create_contract': True,
            'read_contract': True,
            'update_contract': True,
            'delete_contract': True,
            'create_event': True,
            'read_event': True,
            'update_event': True,
            'delete_event': True,
            'create_user': True,
            'read_user': True,
            'update_user': True,
            'delete_user': True,
        }
    }

    @classmethod
    def has_permission(cls, user: User, permission: str) -> bool:
        """Vérifier si l'utilisateur a une permission spécifique"""
        if not user or not user.department:
            return False

        dept_permissions = cls.PERMISSIONS.get(user.department, {})
        return dept_permissions.get(permission, False)

    @classmethod
    def can_access_resource(cls, user: User, resource_type: str,
                            resource_owner_id: int = None,
                            assigned_user_id: int = None) -> bool:
        """Vérifier l'accès à une ressource spécifique"""
        if not user:
            return False

        # Gestion a accès à tout
        if user.is_gestion:
            return True

        # Commercial peut accéder à ses propres ressources
        if user.is_commercial and resource_owner_id == user.id:
            return True

        # Support peut accéder aux événements qui lui sont assignés
        if (user.is_support and resource_type == 'event' and
           assigned_user_id == user.id):
            return True

        # Lecture seule pour tous les autres cas
        read_permissions = ['read_client', 'read_contract', 'read_event']
        return any(cls.has_permission(user, perm) for perm in read_permissions)
