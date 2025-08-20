from typing import Optional
from sqlalchemy.orm import Session
from src.models.user import User, Department
from src.utils.hash_utils import hash_password, verify_password
from .base_controller import BaseController


class AuthController(BaseController):
    """Contrôleur d'authentification - Pattern MVC"""

    def __init__(self, db_session: Session):
        super().__init__(db_session)

    def login(self, email: str, password: str) -> Optional[User]:
        """Connexion utilisateur"""
        try:
            user = self.db.query(User).filter(User.email == email).first()
            if user and verify_password(user.hashed_password, password):
                self.set_current_user(user)
                return user
            return None
        except Exception as e:
            print(f"Erreur lors de la connexion: {e}")
            return None

    def create_user(self, email: str, password: str, full_name: str,
                    department: Department) -> Optional[User]:
        """Créer un utilisateur (gestion uniquement)"""
        if not self.has_permission([Department.GESTION]):
            raise PermissionError("Seule la gestion peut créer des utilisateurs")

        # Vérifier si email existe
        existing_user = self.db.query(User).filter(User.email == email).first()
        if existing_user:
            raise ValueError("Cet email est déjà utilisé")

        try:
            hashed_pwd = hash_password(password)
            user = User(
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
            print(f"Erreur création utilisateur: {e}")
            return None

    def get_all_users(self) -> list:
        """Récupérer tous les utilisateurs (gestion uniquement)"""
        if not self.has_permission([Department.GESTION]):
            raise PermissionError("Accès refusé")
        return self.db.query(User).all()

    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Modifier un utilisateur (gestion uniquement)"""
        if not self.has_permission([Department.GESTION]):
            raise PermissionError("Accès refusé")

        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return None

            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)

            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as e:
            self.db.rollback()
            print(f"Erreur modification utilisateur: {e}")
            return None

    def delete_user(self, user_id: int) -> bool:
        """Supprimer un utilisateur (gestion uniquement)"""
        if not self.has_permission([Department.GESTION]):
            raise PermissionError("Accès refusé")

        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return False

            self.db.delete(user)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Erreur suppression utilisateur: {e}")
            return False

    def logout(self):
        """Déconnexion"""
        self.current_user = None
