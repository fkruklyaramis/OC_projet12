from sqlalchemy.orm import Session
from src.models.user import User, Department


class BaseController:
    """Contrôleur de base - Pattern MVC"""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.current_user = None

    def set_current_user(self, user: User):
        """Définir l'utilisateur connecté"""
        self.current_user = user

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
