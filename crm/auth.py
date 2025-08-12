"""Service d'authentification et de permissions pour Epic Events"""
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError

# Import sécurisé du modèle User
try:
    User = get_user_model()
except Exception:
    User = None


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
                    first_name, last_name):
        """
        Crée un nouvel utilisateur avec tous les éléments d'identification requis
        """
        if not User:
            raise Exception("Modèle User non disponible")

        # Validation des champs obligatoires
        if not all([username, email, password, role, employee_number, first_name, last_name]):
            raise ValidationError("Tous les champs sont obligatoires")

        # Validation du rôle/département
        valid_roles = ['COMMERCIAL', 'SUPPORT', 'GESTION']
        if role not in valid_roles:
            raise ValidationError(f"Rôle invalide. Doit être un de: {valid_roles}")

        # Vérifier l'unicité du numéro d'employé
        if User.objects.filter(employee_number=employee_number).exists():
            raise ValidationError("Ce numéro d'employé existe déjà")

        # Créer l'utilisateur
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
    """Service pour gérer les permissions selon le département"""

    @staticmethod
    def can_create_clients(user):
        """Commercial et Gestion peuvent créer des clients"""
        return user.role in ['COMMERCIAL', 'GESTION']

    @staticmethod
    def can_view_all_clients(user):
        """Tous peuvent voir les clients (lecture seule)"""
        return True

    @staticmethod
    def can_update_client(user, client):
        """Commercial peut modifier ses clients, Gestion tous"""
        if user.role == 'GESTION':
            return True
        if user.role == 'COMMERCIAL':
            return client.sales_contact == user
        return False

    @staticmethod
    def can_create_contracts(user):
        """Seule la Gestion peut créer des contrats"""
        return user.role == 'GESTION'

    @staticmethod
    def can_update_contract(user, contract):
        """Gestion peut modifier tous, Commercial ses contrats"""
        if user.role == 'GESTION':
            return True
        if user.role == 'COMMERCIAL':
            return contract.sales_contact == user
        return False

    @staticmethod
    def can_create_events(user):
        """Commercial peut créer des événements pour ses clients"""
        return user.role in ['COMMERCIAL', 'GESTION']

    @staticmethod
    def can_assign_support(user):
        """Seule la Gestion peut assigner des supports"""
        return user.role == 'GESTION'

    @staticmethod
    def can_update_event(user, event):
        """Support peut modifier ses événements, Gestion tous"""
        if user.role == 'GESTION':
            return True
        if user.role == 'SUPPORT':
            return event.support_contact == user
        return False

    @staticmethod
    def can_manage_users(user):
        """Seule la Gestion peut gérer les utilisateurs"""
        return user.role == 'GESTION'

    @staticmethod
    def get_user_permissions(user):
        """Retourne la liste des permissions de l'utilisateur"""
        permissions = ['view_all_data']  # Tous peuvent voir

        if user.role == 'COMMERCIAL':
            permissions.extend([
                'create_clients',
                'update_own_clients',
                'update_own_contracts',
                'create_events'
            ])
        elif user.role == 'SUPPORT':
            permissions.extend([
                'update_own_events'
            ])
        elif user.role == 'GESTION':
            permissions.extend([
                'create_clients',
                'update_all_clients',
                'create_contracts',
                'update_all_contracts',
                'create_events',
                'assign_support',
                'update_all_events',
                'manage_users'
            ])

        return permissions
