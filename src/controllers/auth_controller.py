from typing import Optional, List
from sqlalchemy.orm import Session
from src.models.user import User, Department
from src.utils.hash_utils import hash_password, verify_password
from src.utils.auth_utils import (
    generate_employee_number, validate_password_strength,
    AuthenticationError, AuthorizationError, PermissionChecker
)
from .base_controller import BaseController


class AuthController(BaseController):
    """Contrôleur d'authentification et autorisation - Pattern MVC"""

    def __init__(self, db_session: Session):
        super().__init__(db_session)
        self.permission_checker = PermissionChecker()

    def authenticate_user(self, email: str, password: str) -> User:
        """Authentifier un utilisateur (séparé de login pour sécurité)"""
        try:
            user = self.db.query(User).filter(User.email == email).first()
            if not user:
                raise AuthenticationError("Utilisateur non trouvé")

            if not verify_password(user.hashed_password, password):
                raise AuthenticationError("Mot de passe incorrect")

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
                raise ValueError("Utilisateur non trouvé")

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
            raise ValueError("Utilisateur non trouvé")

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
                raise ValueError("Utilisateur non trouvé")

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
