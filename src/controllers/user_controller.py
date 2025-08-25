from typing import List, Optional
from sqlalchemy.orm import Session
from src.models.user import User, Department
from src.utils.auth_utils import AuthorizationError, PermissionChecker
from src.utils.validators import DataValidator, ValidationError
from src.utils.hash_utils import hash_password
from .base_controller import BaseController


class UserController(BaseController):
    """Controleur pour la gestion des utilisateurs"""

    def __init__(self, db_session: Session):
        super().__init__(db_session)
        self.permission_checker = PermissionChecker()
        self.validator = DataValidator()

    def create_user(self, employee_number: str, email: str, password: str,
                    full_name: str, department: str) -> User:
        """Creer un nouvel utilisateur"""
        if not self.permission_checker.has_permission(self.current_user, 'create_user'):
            raise AuthorizationError("Permission requise pour créer des utilisateurs")

        try:
            # Validation des données
            validated_employee_number = self.validator.validate_employee_number(employee_number)
            validated_email = self.validator.validate_email(email)
            validated_full_name = self.validator.validate_full_name(full_name)
            validated_department = self.validator.validate_department(department)

            # Validation du mot de passe
            if not password or len(password) < 8:
                raise ValidationError("Le mot de passe doit contenir au moins 8 caractères")

            # Vérifier l'unicité de l'email
            existing_email = self.db.query(User).filter(User.email == validated_email).first()
            if existing_email:
                raise ValidationError("Un utilisateur avec cet email existe déjà")

            # Vérifier l'unicité du numéro d'employé
            existing_employee = self.db.query(User).filter(
                User.employee_number == validated_employee_number
            ).first()
            if existing_employee:
                raise ValidationError("Un utilisateur avec ce numéro d'employé existe déjà")

            # Créer l'utilisateur
            user = User(
                employee_number=validated_employee_number,
                email=validated_email,
                hashed_password=hash_password(password),
                full_name=validated_full_name,
                department=validated_department
            )

            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user

        except (ValidationError, ValueError) as e:
            self.db.rollback()
            raise ValidationError(str(e))
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erreur lors de la création de l'utilisateur: {e}")

    def update_user(self, user_id: int, **kwargs) -> User:
        """Modifier un utilisateur"""
        if not self.permission_checker.has_permission(self.current_user, 'update_user'):
            raise AuthorizationError("Permission requise pour modifier les utilisateurs")

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("Utilisateur non trouvé")

        try:
            # Validation et mise à jour des champs
            if 'employee_number' in kwargs:
                validated_number = self.validator.validate_employee_number(
                    kwargs['employee_number']
                )
                # Vérifier l'unicité
                existing = self.db.query(User).filter(
                    User.employee_number == validated_number,
                    User.id != user_id
                ).first()
                if existing:
                    raise ValidationError("Ce numéro d'employé est déjà utilisé")
                user.employee_number = validated_number

            if 'email' in kwargs:
                validated_email = self.validator.validate_email(kwargs['email'])
                # Vérifier l'unicité
                existing = self.db.query(User).filter(
                    User.email == validated_email,
                    User.id != user_id
                ).first()
                if existing:
                    raise ValidationError("Cet email est déjà utilisé")
                user.email = validated_email

            if 'full_name' in kwargs:
                user.full_name = self.validator.validate_full_name(kwargs['full_name'])

            if 'department' in kwargs:
                user.department = self.validator.validate_department(kwargs['department'])

            if 'password' in kwargs:
                password = kwargs['password']
                if len(password) < 8:
                    raise ValidationError("Le mot de passe doit contenir au moins 8 caractères")
                user.hashed_password = hash_password(password)

            self.db.commit()
            self.db.refresh(user)
            return user

        except (ValidationError, ValueError) as e:
            self.db.rollback()
            raise ValidationError(str(e))
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erreur lors de la modification de l'utilisateur: {e}")

    def get_all_users(self) -> List[User]:
        """Recuperer tous les utilisateurs"""
        if not self.permission_checker.has_permission(self.current_user, 'read_user'):
            raise AuthorizationError("Permission requise pour consulter les utilisateurs")

        return self.db.query(User).all()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Recuperer un utilisateur par son ID"""
        if not self.permission_checker.has_permission(self.current_user, 'read_user'):
            raise AuthorizationError("Permission requise pour consulter les utilisateurs")

        return self.db.query(User).filter(User.id == user_id).first()

    def get_users_by_department(self, department: Department) -> List[User]:
        """Recuperer les utilisateurs d'un département"""
        if not self.permission_checker.has_permission(self.current_user, 'read_user'):
            raise AuthorizationError("Permission requise pour consulter les utilisateurs")

        return self.db.query(User).filter(User.department == department).all()

    def delete_user(self, user_id: int) -> bool:
        """Supprimer un utilisateur"""
        if not self.permission_checker.has_permission(self.current_user, 'delete_user'):
            raise AuthorizationError("Permission requise pour supprimer des utilisateurs")

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("Utilisateur non trouvé")

        # Ne pas permettre la suppression de soi-même
        if user.id == self.current_user.id:
            raise ValidationError("Vous ne pouvez pas supprimer votre propre compte")

        try:
            self.db.delete(user)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erreur lors de la suppression de l'utilisateur: {e}")
