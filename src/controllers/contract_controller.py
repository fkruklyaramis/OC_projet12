from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from src.models.contract import Contract, ContractStatus
from src.models.client import Client
from src.models.user import User
from src.utils.auth_utils import AuthorizationError, PermissionChecker
from src.utils.validators import DataValidator, ValidationError
from .base_controller import BaseController


class ContractController(BaseController):
    """Controleur pour la gestion des contrats - Pattern MVC"""

    def __init__(self, db_session: Session):
        super().__init__(db_session)
        self.permission_checker = PermissionChecker()
        self.validator = DataValidator()

    def create_contract(self, client_id: int, total_amount: float, amount_due: float = None) -> Contract:
        """Creer un nouveau contrat"""
        if not self.permission_checker.has_permission(self.current_user, 'create_contract'):
            raise AuthorizationError("Permission requise pour créer des contrats")

        try:
            # Validation des données
            validated_total_amount = self.validator.validate_amount(total_amount, "Montant total")

            if amount_due is not None:
                validated_amount_due = self.validator.validate_amount(amount_due, "Montant dû")
                if validated_amount_due > validated_total_amount:
                    raise ValidationError("Le montant dû ne peut pas être supérieur au montant total")
            else:
                validated_amount_due = validated_total_amount

            # Vérifier que le client existe
            client = self.db.query(Client).filter(Client.id == client_id).first()
            if not client:
                raise ValidationError("Client non trouvé")

            # Seul le commercial du client ou la gestion peut créer des contrats
            if (self.current_user.is_commercial and
               client.commercial_contact_id != self.current_user.id and not self.current_user.is_gestion):
                raise AuthorizationError("Vous ne pouvez créer des contrats que pour vos clients")

            # Créer le contrat
            contract = Contract(
                client_id=client_id,
                commercial_contact_id=client.commercial_contact_id,
                total_amount=validated_total_amount,
                amount_due=validated_amount_due,
                status=ContractStatus.DRAFT
            )

            self.db.add(contract)
            self.db.commit()
            self.db.refresh(contract)
            return contract

        except (ValidationError, ValueError) as e:
            self.db.rollback()
            raise ValidationError(str(e))
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erreur lors de la création du contrat: {e}")

    def update_contract(self, contract_id: int, **kwargs) -> Contract:
        """Modifier un contrat"""
        if not self.permission_checker.has_permission(self.current_user, 'update_contract'):
            if not (self.current_user.is_commercial and
                    self.permission_checker.has_permission(self.current_user, 'update_own_contract')):
                raise AuthorizationError("Permission requise pour modifier les contrats")

        contract = self.get_contract_by_id(contract_id)
        if not contract:
            raise ValueError("Contrat non trouvé")

        if not self._can_access_contract(contract):
            raise AuthorizationError("Accès refusé à ce contrat")

        try:
            # Validation et mise à jour des champs
            if 'total_amount' in kwargs:
                validated_amount = self.validator.validate_amount(
                    kwargs['total_amount'], "Montant total"
                )
                # Vérifier que le nouveau montant total >= montant dû
                if validated_amount < contract.amount_due:
                    raise ValidationError(
                        "Le montant total ne peut pas être inférieur au montant dû"
                    )
                contract.total_amount = validated_amount

            if 'amount_due' in kwargs:
                validated_due = self.validator.validate_amount(
                    kwargs['amount_due'], "Montant dû"
                )
                # Vérifier que montant dû <= montant total
                total_amount = kwargs.get('total_amount', contract.total_amount)
                if validated_due > total_amount:
                    raise ValidationError(
                        "Le montant dû ne peut pas être supérieur au montant total"
                    )
                contract.amount_due = validated_due

            if 'status' in kwargs:
                validated_status = self.validator.validate_contract_status(kwargs['status'])
                contract.status = validated_status

            if 'signed' in kwargs:
                signed = kwargs['signed']
                if not isinstance(signed, bool):
                    raise ValidationError("Le statut de signature doit être un booléen")

                if signed and not contract.signed:
                    # Contrat signé : mettre à jour la date et le statut
                    contract.signed = True
                    contract.signed_at = datetime.now()
                    contract.status = ContractStatus.SIGNED
                elif not signed and contract.signed:
                    # Contrat non signé : remettre en brouillon
                    contract.signed = False
                    contract.signed_at = None
                    contract.status = ContractStatus.DRAFT

            # Seule la gestion peut changer l'assignation commercial
            if 'commercial_contact_id' in kwargs:
                if not self.current_user.is_gestion:
                    raise AuthorizationError(
                        "Seule la gestion peut changer l'assignation commerciale"
                    )

                commercial_id = kwargs['commercial_contact_id']
                commercial = self.db.query(User).filter(User.id == commercial_id).first()
                if not commercial or not commercial.is_commercial:
                    raise ValidationError("Le contact commercial spécifié n'existe pas")

                contract.commercial_contact_id = commercial_id

            self.db.commit()
            self.db.refresh(contract)
            return contract

        except (ValidationError, ValueError) as e:
            self.db.rollback()
            raise ValidationError(str(e))
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erreur lors de la modification du contrat: {e}")

    def get_all_contracts(self) -> List[Contract]:
        """Recuperer tous les contrats avec verification des permissions"""
        if not self.permission_checker.has_permission(self.current_user, 'read_contract'):
            raise AuthorizationError("Permission requise pour consulter les contrats")

        # Seule la gestion peut voir TOUS les contrats
        if not self.current_user.is_gestion:
            raise AuthorizationError("Seule la gestion peut consulter tous les contrats")

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
            raise AuthorizationError("Accès refusé à ce contrat")

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

        # Filtre par role utilisateur
        if self.current_user.is_commercial:
            query = query.filter(Contract.commercial_contact_id == self.current_user.id)
        elif self.current_user.is_support:
            # Support peut voir les contrats avec des evenements assignes
            from src.models.event import Event
            query = query.join(Event).filter(Event.support_contact_id == self.current_user.id)

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

        # Filtre par role utilisateur
        if self.current_user.is_commercial:
            query = query.filter(Contract.commercial_contact_id == self.current_user.id)
        elif self.current_user.is_support:
            from src.models.event import Event
            query = query.join(Event).filter(Event.support_contact_id == self.current_user.id)

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

        # Filtre par role utilisateur
        if self.current_user.is_commercial:
            query = query.filter(Contract.commercial_contact_id == self.current_user.id)
        elif self.current_user.is_support:
            from src.models.event import Event
            query = query.join(Event).filter(Event.support_contact_id == self.current_user.id)

        return query.all()

    def _can_access_contract(self, contract: Contract) -> bool:
        """Verifier si l'utilisateur peut acceder a ce contrat"""
        if self.current_user.is_gestion:
            return True

        if self.current_user.is_commercial:
            return contract.commercial_contact_id == self.current_user.id

        if self.current_user.is_support:
            # Support peut voir les contrats avec des evenements assignes
            return any(event.support_contact_id == self.current_user.id for event in contract.events)

        return False
