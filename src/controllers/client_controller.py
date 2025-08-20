from typing import List, Optional
from sqlalchemy.orm import Session
from src.models.client import Client
from src.models.user import Department
from .base_controller import BaseController


class ClientController(BaseController):
    """Contrôleur pour la gestion des clients - Pattern MVC"""

    def __init__(self, db_session: Session):
        super().__init__(db_session)

    def create_client(self, full_name: str, email: str, phone: str,
                      company_name: str) -> Optional[Client]:
        """Créer un client (commercial uniquement)"""
        if not self.has_permission([Department.COMMERCIAL]):
            raise PermissionError("Seuls les commerciaux peuvent créer des clients")

        # Vérifier si email existe
        existing_client = self.db.query(Client).filter(Client.email == email).first()
        if existing_client:
            raise ValueError("Un client avec cet email existe déjà")

        try:
            client = Client(
                full_name=full_name,
                email=email,
                phone=phone,
                company_name=company_name,
                commercial_contact_id=self.current_user.id
            )
            self.db.add(client)
            self.db.commit()
            self.db.refresh(client)
            return client
        except Exception as e:
            self.db.rollback()
            print(f"Erreur création client: {e}")
            return None

    def get_all_clients(self) -> List[Client]:
        """Récupérer tous les clients (lecture pour tous)"""
        return self.db.query(Client).all()

    def get_my_clients(self) -> List[Client]:
        """Récupérer mes clients (commercial)"""
        if not self.has_permission([Department.COMMERCIAL]):
            raise PermissionError("Accès refusé")

        return self.db.query(Client).filter(
            Client.commercial_contact_id == self.current_user.id
        ).all()

    def get_client_by_id(self, client_id: int) -> Optional[Client]:
        """Récupérer un client par ID"""
        return self.db.query(Client).filter(Client.id == client_id).first()

    def update_client(self, client_id: int, **kwargs) -> Optional[Client]:
        """Modifier un client"""
        client = self.get_client_by_id(client_id)
        if not client:
            return None

        # Vérifier permissions
        if not (self.has_permission([Department.GESTION]) or
                (self.has_permission([Department.COMMERCIAL]) and
                 client.commercial_contact_id == self.current_user.id)):
            raise PermissionError("Vous ne pouvez modifier que vos clients")

        try:
            for key, value in kwargs.items():
                if hasattr(client, key) and key != 'id':
                    setattr(client, key, value)

            self.db.commit()
            self.db.refresh(client)
            return client
        except Exception as e:
            self.db.rollback()
            print(f"Erreur modification client: {e}")
            return None

    def delete_client(self, client_id: int) -> bool:
        """Supprimer un client (gestion uniquement)"""
        if not self.has_permission([Department.GESTION]):
            raise PermissionError("Seule la gestion peut supprimer des clients")

        try:
            client = self.get_client_by_id(client_id)
            if not client:
                return False

            self.db.delete(client)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Erreur suppression client: {e}")
            return False

    def search_clients(self, **criteria) -> List[Client]:
        """Rechercher des clients par critères"""
        query = self.db.query(Client)

        if 'company_name' in criteria:
            query = query.filter(Client.company_name.contains(criteria['company_name']))
        if 'full_name' in criteria:
            query = query.filter(Client.full_name.contains(criteria['full_name']))
        if 'email' in criteria:
            query = query.filter(Client.email.contains(criteria['email']))

        return query.all()
