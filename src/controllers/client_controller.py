from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from src.models.client import Client
from src.models.user import Department
from src.utils.auth_utils import AuthorizationError
from src.utils.validators import ValidationError
from .base_controller import BaseController


class ClientController(BaseController):
    """Controleur pour la gestion des clients - Pattern MVC"""

    def __init__(self, db_session: Session):
        super().__init__(db_session)

    def create_client(self, full_name: str, email: str, phone: str,
                      company_name: str, commercial_contact_id: int = None) -> Client:
        """Créer un nouveau client avec validation complète"""
        if not self.permission_checker.has_permission(self.current_user, 'create_client'):
            raise AuthorizationError("Permission 'create_client' requise")

        # Validation des données avec vérification d'unicité email
        try:
            validated_email = self.validate_and_check_unique_email(email, Client)
            validated_phone = self.validator.validate_phone(phone)
            validated_full_name = self.validator.validate_full_name(full_name)
            validated_company_name = self.validator.validate_company_name(company_name)
        except ValidationError as e:
            raise ValidationError(f"Validation échouée: {e}")

        # Déterminer le commercial responsable
        if not commercial_contact_id:
            if self.current_user.is_commercial:
                commercial_contact_id = self.current_user.id
            else:
                raise ValidationError("Un commercial responsable doit être spécifié")

        # Vérifier que le commercial existe
        self.get_user_by_id_and_department(commercial_contact_id, Department.COMMERCIAL)

        # Commercial ne peut créer que pour lui-même
        if self.current_user.is_commercial and commercial_contact_id != self.current_user.id:
            raise AuthorizationError("Vous ne pouvez créer des clients que pour vous-même")

        try:
            client = Client(
                full_name=validated_full_name,
                email=validated_email,
                phone=validated_phone,
                company_name=validated_company_name,
                commercial_contact_id=commercial_contact_id
            )

            self.db.add(client)
            self.safe_commit()
            self.db.refresh(client)
            return client

        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erreur lors de la création: {e}")

    def update_client(self, client_id: int, **update_data) -> Client:
        """Mettre à jour un client avec validation"""
        client = self.get_client_by_id(client_id)
        if not client:
            raise ValidationError("Client non trouvé")

        self.require_write_access('client', client)

        try:
            # Validation centralisée des champs communs
            validated_data = self.validate_update_fields(update_data, Client, client_id)

            # Vérifier le changement de commercial (gestion uniquement)
            if 'commercial_contact_id' in update_data:
                if not self.current_user.is_gestion:
                    raise AuthorizationError("Seule la gestion peut réassigner des clients")

                self.get_user_by_id_and_department(
                    update_data['commercial_contact_id'], Department.COMMERCIAL
                )
                validated_data['commercial_contact_id'] = update_data['commercial_contact_id']

            # Appliquer les mises à jour validées
            self.apply_validated_updates(client, validated_data)

            self.safe_commit()
            self.db.refresh(client)
            return client

        except ValidationError:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erreur lors de la mise à jour: {e}")

    def get_all_clients(self) -> List[Client]:
        """Recuperer tous les clients avec verification des permissions"""
        self.require_read_access('client')

        if not self.current_user.is_gestion:
            raise AuthorizationError("Seule la gestion peut consulter tous les clients")

        return self.db.query(Client).options(
            joinedload(Client.commercial_contact)
        ).all()

    def get_my_clients(self) -> List[Client]:
        """Recuperer les clients assignes a l'utilisateur actuel"""
        self.require_authentication()

        if not self.current_user.is_commercial:
            raise AuthorizationError("Seuls les commerciaux peuvent consulter leurs clients")

        query = self.db.query(Client).options(joinedload(Client.commercial_contact))
        return self.get_filtered_query_by_role(query, 'client').all()

    def get_client_by_id(self, client_id: int) -> Optional[Client]:
        """Recuperer un client par son ID avec verification d'acces"""
        self.require_read_access('client')

        client = self.db.query(Client).options(
            joinedload(Client.commercial_contact),
            joinedload(Client.contracts)
        ).filter(Client.id == client_id).first()

        if client and not self._can_access_client(client):
            raise AuthorizationError("Accès refusé à ce client")

        return client

    def search_clients(self, **criteria) -> List[Client]:
        """Rechercher des clients selon des criteres"""
        self.require_read_access('client')

        query = self.db.query(Client).options(joinedload(Client.commercial_contact))

        # Appliquer les filtres de recherche génériques
        searchable_fields = ['full_name', 'email', 'company_name']
        query = self.search_with_filters(query, Client, criteria, searchable_fields)

        # Appliquer le filtre par rôle utilisateur
        if self.current_user.is_support:
            # Support peut rechercher dans les clients avec des événements assignés
            from src.models.contract import Contract
            from src.models.event import Event
            query = query.join(Contract).join(Event).filter(
                Event.support_contact_id == self.current_user.id
            )
        else:
            query = self.get_filtered_query_by_role(query, 'client')

        return query.all()

    def _can_access_client(self, client: Client) -> bool:
        """Verifier si l'utilisateur peut acceder a ce client"""
        if self.current_user.is_gestion:
            return True

        if self.current_user.is_commercial:
            return client.commercial_contact_id == self.current_user.id

        if self.current_user.is_support:
            # Support peut voir les clients avec des événements assignés
            from src.models.contract import Contract
            from src.models.event import Event
            return self.db.query(Contract).join(Event).filter(
                Contract.client_id == client.id,
                Event.support_contact_id == self.current_user.id
            ).first() is not None

        return False
