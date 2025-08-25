from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from src.models.client import Client
from src.models.user import User
from src.utils.auth_utils import AuthorizationError, PermissionChecker
from src.utils.validators import DataValidator, ValidationError
from .base_controller import BaseController


class ClientController(BaseController):
    """Controleur pour la gestion des clients - Pattern MVC"""

    def __init__(self, db_session: Session):
        super().__init__(db_session)
        self.permission_checker = PermissionChecker()
        self.validator = DataValidator()

    def create_client(self, full_name: str, email: str, phone: str,
                      company_name: str, commercial_contact_id: int = None) -> Client:
        """Creer un nouveau client"""
        if not self.permission_checker.has_permission(self.current_user, 'create_client'):
            raise AuthorizationError("Permission requise pour créer des clients")

        try:
            # Validation des données
            validated_full_name = self.validator.validate_full_name(full_name)
            validated_email = self.validator.validate_email(email)
            validated_phone = self.validator.validate_phone(phone)
            validated_company_name = self.validator.validate_company_name(company_name)

            # Vérifier l'unicité de l'email
            existing_email = self.db.query(Client).filter(Client.email == validated_email).first()
            if existing_email:
                raise ValidationError("Un client avec cet email existe déjà")

            # Déterminer le commercial assigné
            if commercial_contact_id:
                # Vérifier que le commercial existe
                commercial = self.db.query(User).filter(User.id == commercial_contact_id).first()
                if not commercial or not commercial.is_commercial:
                    raise ValidationError("Le contact commercial spécifié n'existe pas")

                # Seule la gestion peut assigner à un autre commercial
                if (self.current_user.is_commercial and
                   commercial_contact_id != self.current_user.id and not self.current_user.is_gestion):
                    raise AuthorizationError(
                        "Vous ne pouvez assigner des clients qu'à vous-même"
                    )
            else:
                # Si pas de commercial spécifié, assigner à l'utilisateur actuel s'il est commercial
                if self.current_user.is_commercial:
                    commercial_contact_id = self.current_user.id
                else:
                    raise ValidationError("Vous devez spécifier un contact commercial")

            # Créer le client
            client = Client(
                full_name=validated_full_name,
                email=validated_email,
                phone=validated_phone,
                company_name=validated_company_name,
                commercial_contact_id=commercial_contact_id
            )

            self.db.add(client)
            self.db.commit()
            self.db.refresh(client)
            return client

        except (ValidationError, ValueError) as e:
            self.db.rollback()
            raise ValidationError(str(e))
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erreur lors de la création du client: {e}")

    def update_client(self, client_id: int, **kwargs) -> Client:
        """Modifier un client"""
        if not self.permission_checker.has_permission(self.current_user, 'update_client'):
            if not (self.current_user.is_commercial and
                    self.permission_checker.has_permission(self.current_user, 'update_own_client')):
                raise AuthorizationError("Permission requise pour modifier les clients")

        client = self.get_client_by_id(client_id)
        if not client:
            raise ValueError("Client non trouvé")

        if not self._can_access_client(client):
            raise AuthorizationError("Accès refusé à ce client")

        try:
            # Validation et mise à jour des champs
            if 'full_name' in kwargs:
                client.full_name = self.validator.validate_full_name(kwargs['full_name'])

            if 'email' in kwargs:
                validated_email = self.validator.validate_email(kwargs['email'])
                # Vérifier l'unicité
                existing = self.db.query(Client).filter(
                    Client.email == validated_email,
                    Client.id != client_id
                ).first()
                if existing:
                    raise ValidationError("Cet email est déjà utilisé par un autre client")
                client.email = validated_email

            if 'phone' in kwargs:
                client.phone = self.validator.validate_phone(kwargs['phone'])

            if 'company_name' in kwargs:
                client.company_name = self.validator.validate_company_name(kwargs['company_name'])

            if 'commercial_contact_id' in kwargs:
                # Seule la gestion peut changer l'assignation commercial
                if not self.current_user.is_gestion:
                    raise AuthorizationError(
                        "Seule la gestion peut changer l'assignation commerciale"
                    )

                commercial_id = kwargs['commercial_contact_id']
                commercial = self.db.query(User).filter(User.id == commercial_id).first()
                if not commercial or not commercial.is_commercial:
                    raise ValidationError("Le contact commercial spécifié n'existe pas")

                client.commercial_contact_id = commercial_id

            self.db.commit()
            self.db.refresh(client)
            return client

        except (ValidationError, ValueError) as e:
            self.db.rollback()
            raise ValidationError(str(e))
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erreur lors de la modification du client: {e}")

    def get_all_clients(self) -> List[Client]:
        """Recuperer tous les clients avec verification des permissions"""
        if not self.permission_checker.has_permission(self.current_user, 'read_client'):
            raise AuthorizationError("Permission requise pour consulter les clients")

        if not self.current_user.is_gestion:
            raise AuthorizationError("Seule la gestion peut consulter tous les clients")

        return self.db.query(Client).options(
            joinedload(Client.commercial_contact)
        ).all()

    def get_my_clients(self) -> List[Client]:
        """Recuperer les clients assignes a l'utilisateur actuel"""
        if not self.current_user:
            raise AuthorizationError("Authentification requise")

        if not self.current_user.is_commercial:
            raise AuthorizationError("Seuls les commerciaux peuvent consulter leurs clients")

        return self.db.query(Client).options(
            joinedload(Client.commercial_contact)
        ).filter(Client.commercial_contact_id == self.current_user.id).all()

    def get_client_by_id(self, client_id: int) -> Optional[Client]:
        """Recuperer un client par son ID avec verification d'acces"""
        if not self.permission_checker.has_permission(self.current_user, 'read_client'):
            raise AuthorizationError("Permission requise pour consulter les clients")

        client = self.db.query(Client).options(
            joinedload(Client.commercial_contact),
            joinedload(Client.contracts)
        ).filter(Client.id == client_id).first()

        if client and not self._can_access_client(client):
            raise AuthorizationError("Accès refusé à ce client")

        return client

    def search_clients(self, **criteria) -> List[Client]:
        """Rechercher des clients selon des criteres"""
        if not self.permission_checker.has_permission(self.current_user, 'read_client'):
            raise AuthorizationError("Permission requise pour consulter les clients")

        query = self.db.query(Client).options(joinedload(Client.commercial_contact))

        # Filtres de recherche
        if 'full_name' in criteria and criteria['full_name']:
            query = query.filter(Client.full_name.ilike(f"%{criteria['full_name']}%"))

        if 'email' in criteria and criteria['email']:
            query = query.filter(Client.email.ilike(f"%{criteria['email']}%"))

        if 'company_name' in criteria and criteria['company_name']:
            query = query.filter(Client.company_name.ilike(f"%{criteria['company_name']}%"))

        # Filtre par role utilisateur
        if self.current_user.is_commercial:
            query = query.filter(Client.commercial_contact_id == self.current_user.id)
        elif self.current_user.is_support:
            # Support peut rechercher dans les clients avec des événements assignés
            from src.models.contract import Contract
            from src.models.event import Event
            query = query.join(Contract).join(Event).filter(
                Event.support_contact_id == self.current_user.id
            )

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
