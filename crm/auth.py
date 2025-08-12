"""Service d'authentification et de permissions pour Epic Events"""
from django.contrib.auth import authenticate, get_user_model

User = get_user_model()


class AuthService:
    """Service pour l'authentification"""

    @staticmethod
    def authenticate_user(username, password):
        """Authentifie un utilisateur"""
        user = authenticate(username=username, password=password)
        if user and user.is_active:
            return user
        return None

    @staticmethod
    def create_user(username, email, password, role, employee_number,
                    first_name="", last_name=""):
        """Crée un nouvel utilisateur"""
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=role,
            employee_number=employee_number,
            first_name=first_name,
            last_name=last_name
        )
        return user


class PermissionService:
    """Service séparé pour gérer les permissions"""

    @staticmethod
    def can_create_clients(user):
        """Vérifie si l'utilisateur peut créer des clients"""
        return user.role in ['COMMERCIAL', 'GESTION']

    @staticmethod
    def can_manage_contracts(user):
        """Vérifie si l'utilisateur peut gérer tous les contrats"""
        return user.role == 'GESTION'

    @staticmethod
    def can_assign_support(user):
        """Vérifie si l'utilisateur peut assigner des supports"""
        return user.role == 'GESTION'

    @staticmethod
    def can_update_client(user, client):
        """Vérifie si l'utilisateur peut modifier ce client"""
        if user.role == 'GESTION':
            return True
        if user.role == 'COMMERCIAL':
            return client.sales_contact == user
        return False

    @staticmethod
    def can_update_event(user, event):
        """Vérifie si l'utilisateur peut modifier cet événement"""
        if user.role == 'GESTION':
            return True
        if user.role == 'SUPPORT':
            return event.support_contact == user
        return False
