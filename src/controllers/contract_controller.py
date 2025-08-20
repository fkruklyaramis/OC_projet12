from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from src.models.contract import Contract, ContractStatus
from src.models.client import Client
from src.models.user import User, Department
from src.utils.auth_utils import AuthorizationError, PermissionChecker
from .base_controller import BaseController


class ContractController(BaseController):
    """Controleur pour la gestion des contrats - Pattern MVC"""

    def __init__(self, db_session: Session):
        super().__init__(db_session)
        self.permission_checker = PermissionChecker()

    def get_all_contracts(self) -> List[Contract]:
        """Recuperer tous les contrats avec verification des permissions"""
        if not self.permission_checker.has_permission(self.current_user, 'read_contract'):
            raise AuthorizationError("Permission requise pour consulter les contrats")
        
        return self.db.query(Contract).options(
            joinedload(Contract.client),
            joinedload(Contract.commercial_contact)
        ).all()

    def get_contract_by_id(self, contract_id: int) -> Optional[Contract]:
        """Recuperer un contrat par son ID avec verification d'acces"""
        if not self.permission_checker.has_permission(self.current_user, 'read_contract'):
            raise AuthorizationError("Permission requise pour consulter les contrats")
        
        contract = self.db.query(Contract).options(
            joinedload(Contract.client),
            joinedload(Contract.commercial_contact),
            joinedload(Contract.events)
        ).filter(Contract.id == contract_id).first()
        
        if contract and not self._can_access_contract(contract):
            raise AuthorizationError("Acces refuse a ce contrat")
        
        return contract

    def get_my_contracts(self) -> List[Contract]:
        """Recuperer les contrats assignes a l'utilisateur actuel"""
        if not self.current_user:
            raise AuthorizationError("Authentification requise")
        
        if not self.current_user.is_commercial:
            raise AuthorizationError("Seuls les commerciaux peuvent consulter leurs contrats")
        
        return self.db.query(Contract).options(
            joinedload(Contract.client),
            joinedload(Contract.commercial_contact)
        ).filter(Contract.commercial_contact_id == self.current_user.id).all()

    def get_contracts_by_status(self, status: ContractStatus) -> List[Contract]:
        """Recuperer les contrats par statut"""
        if not self.permission_checker.has_permission(self.current_user, 'read_contract'):
            raise AuthorizationError("Permission requise pour consulter les contrats")
        
        query = self.db.query(Contract).options(
            joinedload(Contract.client),
            joinedload(Contract.commercial_contact)
        ).filter(Contract.status == status)
        
        # Filtre pour les commerciaux : seulement leurs contrats
        if self.current_user.is_commercial:
            query = query.filter(Contract.commercial_contact_id == self.current_user.id)
        
        return query.all()

    def get_unsigned_contracts(self) -> List[Contract]:
        """Recuperer les contrats non signes"""
        return self.get_contracts_by_status(ContractStatus.DRAFT)

    def get_unpaid_contracts(self) -> List[Contract]:
        """Recuperer les contrats avec des montants dus"""
        if not self.permission_checker.has_permission(self.current_user, 'read_contract'):
            raise AuthorizationError("Permission requise pour consulter les contrats")
        
        query = self.db.query(Contract).options(
            joinedload(Contract.client),
            joinedload(Contract.commercial_contact)
        ).filter(Contract.amount_due > 0)
        
        if self.current_user.is_commercial:
            query = query.filter(Contract.commercial_contact_id == self.current_user.id)
        
        return query.all()

    def search_contracts(self, **criteria) -> List[Contract]:
        """Rechercher des contrats selon des criteres"""
        if not self.permission_checker.has_permission(self.current_user, 'read_contract'):
            raise AuthorizationError("Permission requise pour consulter les contrats")
        
        query = self.db.query(Contract).options(
            joinedload(Contract.client),
            joinedload(Contract.commercial_contact)
        )
        
        # Filtre par client
        if 'client_name' in criteria and criteria['client_name']:
            query = query.join(Client).filter(
                Client.full_name.ilike(f"%{criteria['client_name']}%")
            )
        
        # Filtre par entreprise
        if 'company_name' in criteria and criteria['company_name']:
            query = query.join(Client).filter(
                Client.company_name.ilike(f"%{criteria['company_name']}%")
            )
        
        # Filtre par statut
        if 'status' in criteria and criteria['status']:
            query = query.filter(Contract.status == criteria['status'])
        
        # Filtre pour les commerciaux
        if self.current_user.is_commercial:
            query = query.filter(Contract.commercial_contact_id == self.current_user.id)
        
        return query.all()

    def create_contract(self, client_id: int, total_amount: float, 
                       amount_due: float = None) -> Contract:
        """Creer un nouveau contrat"""
        if not self.permission_checker.has_permission(self.current_user, 'create_contract'):
            raise AuthorizationError("Permission requise pour creer des contrats")
        
        # Verifier que le client existe
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise ValueError("Client non trouve")
        
        # Seul le commercial du client ou la gestion peut creer des contrats
        if (self.current_user.is_commercial and 
            client.commercial_contact_id != self.current_user.id and
            not self.current_user.is_gestion):
            raise AuthorizationError("Vous ne pouvez creer des contrats que pour vos clients")
        
        try:
            contract = Contract(
                client_id=client_id,
                commercial_contact_id=client.commercial_contact_id,
                total_amount=total_amount,
                amount_due=amount_due or total_amount
            )
            self.db.add(contract)
            self.db.commit()
            self.db.refresh(contract)
            return contract
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erreur lors de la creation du contrat: {e}")

    def update_contract(self, contract_id: int, **kwargs) -> Contract:
        """Modifier un contrat"""
        if not self.permission_checker.has_permission(self.current_user, 'update_contract'):
            if not (self.current_user.is_commercial and 
                   self.permission_checker.has_permission(self.current_user, 'update_own_contract')):
                raise AuthorizationError("Permission requise pour modifier les contrats")
        
        contract = self.get_contract_by_id(contract_id)
        if not contract:
            raise ValueError("Contrat non trouve")
        
        if not self._can_access_contract(contract):
            raise AuthorizationError("Acces refuse a ce contrat")
        
        try:
            forbidden_fields = ['id', 'created_at', 'client_id', 'commercial_contact_id']
            for key, value in kwargs.items():
                if key in forbidden_fields:
                    continue
                if hasattr(contract, key):
                    setattr(contract, key, value)
            
            self.db.commit()
            self.db.refresh(contract)
            return contract
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erreur lors de la modification: {e}")

    def _can_access_contract(self, contract: Contract) -> bool:
        """Verifier si l'utilisateur peut acceder a ce contrat"""
        if self.current_user.is_gestion:
            return True
        
        if self.current_user.is_commercial:
            return contract.commercial_contact_id == self.current_user.id
        
        if self.current_user.is_support:
            # Support peut voir les contrats avec des evenements assignes
            return any(event.support_contact_id == self.current_user.id 
                      for event in contract.events)
        
        return False