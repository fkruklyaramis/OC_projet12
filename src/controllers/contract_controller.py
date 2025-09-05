from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session, joinedload
from src.models.contract import Contract, ContractStatus
from src.models.client import Client
from src.utils.auth_utils import AuthorizationError
from src.utils.validators import ValidationError
from src.services.logging_service import SentryLogger
from .base_controller import BaseController


class ContractController(BaseController):
    """Controleur pour la gestion des contrats - Pattern MVC"""

    def __init__(self, db_session: Session):
        super().__init__(db_session)

    def create_contract(self, client_id: int, total_amount: float,
                        amount_due: float = None) -> Contract:
        """Créer un nouveau contrat avec validation"""
        self.require_create_access('contract')

        # Validation des montants
        try:
            validated_total_amount = self.validator.validate_amount(
                total_amount, "Montant total"
            )

            if amount_due is not None:
                validated_amount_due = self.validator.validate_amount(
                    amount_due, "Montant dû"
                )
            else:
                validated_amount_due = validated_total_amount

            # Le montant dû ne peut pas être supérieur au montant total
            if validated_amount_due > validated_total_amount:
                raise ValidationError("Le montant dû ne peut pas être supérieur au montant total")
        except ValidationError as e:
            raise ValidationError(f"Validation des montants: {e}")

        # Vérifier que le client existe
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise ValidationError("Client non trouvé")

        try:
            contract = Contract(
                client_id=client_id,
                total_amount=validated_total_amount,
                amount_due=validated_amount_due,
                status=ContractStatus.DRAFT,
                commercial_contact_id=client.commercial_contact_id
            )

            self.db.add(contract)
            self.safe_commit()
            self.db.refresh(contract)
            return contract

        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erreur lors de la création: {e}")

    def update_contract(self, contract_id: int, **update_data) -> Contract:
        """Mettre à jour un contrat avec validation"""
        contract = self.get_contract_by_id(contract_id)
        if not contract:
            raise ValidationError("Contrat non trouvé")

        self.require_write_access('contract', contract)

        try:
            validated_data = {}

            # Validation des montants
            if 'total_amount' in update_data:
                validated_data['total_amount'] = self.validator.validate_amount(
                    update_data['total_amount'], "Montant total"
                )

            if 'amount_due' in update_data:
                validated_data['amount_due'] = self.validator.validate_amount(
                    update_data['amount_due'], "Montant dû"
                )

            # Vérifier que le montant dû n'est pas supérieur au total
            total = validated_data.get('total_amount', contract.total_amount)
            due = validated_data.get('amount_due', contract.amount_due)

            if due > total:
                raise ValidationError("Le montant dû ne peut pas être supérieur au montant total")

            # Validation du statut et journalisation des signatures
            if 'status' in update_data:
                if isinstance(update_data['status'], str):
                    validated_data['status'] = self.validator.validate_contract_status(
                        update_data['status']
                    )
                else:
                    validated_data['status'] = update_data['status']

                # Vérifier si c'est une signature de contrat
                is_being_signed = (
                    validated_data['status'] == ContractStatus.SIGNED and
                    contract.status != ContractStatus.SIGNED
                )

            # Appliquer les mises à jour
            forbidden_fields = ['id', 'client_id', 'commercial_contact_id',
                                'created_at', 'updated_at']
            self.apply_validated_updates(contract, validated_data, forbidden_fields)

            self.safe_commit()
            self.db.refresh(contract)

            # Journaliser la signature si applicable
            if 'status' in validated_data and is_being_signed:
                print(f"🔥 DEBUG: Tentative log signature contrat {contract.id}")
                print(f"    - Client: {getattr(contract.client, 'company_name', 'NON CHARGÉ')}")
                print(f"    - Commercial: {getattr(self.current_user, 'full_name', 'NON DÉFINI')}")
                try:
                    # Force le chargement des relations
                    self.db.refresh(contract)
                    SentryLogger().log_contract_signature(contract, self.current_user)
                    print("✅ DEBUG: Log signature envoyé avec succès !")
                except Exception as e:
                    print(f"❌ DEBUG: ERREUR lors du log: {e}")
                    import traceback
                    traceback.print_exc()

            return contract

        except ValidationError:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erreur lors de la mise à jour: {e}")

    def get_all_contracts(self) -> List[Contract]:
        """Recuperer tous les contrats avec verification des permissions"""
        self.require_read_access('contract')

        # Seule la gestion peut voir TOUS les contrats
        if not self.current_user.is_gestion:
            raise AuthorizationError("Seule la gestion peut consulter tous les contrats")

        return self.db.query(Contract).options(
            joinedload(Contract.client),
            joinedload(Contract.commercial_contact)
        ).all()

    def get_contract_by_id(self, contract_id: int) -> Optional[Contract]:
        """Recuperer un contrat par son ID avec verification d'acces"""
        self.require_read_access('contract')

        contract = self.db.query(Contract).options(
            joinedload(Contract.client),
            joinedload(Contract.commercial_contact),
            joinedload(Contract.events)
        ).filter(Contract.id == contract_id).first()

        if contract and not self._can_access_contract(contract):
            raise AuthorizationError("Accès refusé à ce contrat")

        return contract

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
            joinedload(Contract.commercial_contact),
            joinedload(Contract.events)
        ).filter(Contract.commercial_contact_id == self.current_user.id).all()

    def sign_contract(self, contract_id: int) -> Contract:
        """Signer un contrat"""
        contract = self.get_contract_by_id(contract_id)
        if not contract:
            raise ValidationError("Contrat non trouvé")

        # Seule la gestion peut signer des contrats
        if not self.current_user.is_gestion:
            raise AuthorizationError("Seule la gestion peut signer des contrats")

        if contract.status == ContractStatus.SIGNED:
            raise ValidationError("Ce contrat est déjà signé")

        contract.status = ContractStatus.SIGNED
        contract.signed_date = datetime.now(timezone.utc)

        self.safe_commit()
        self.db.refresh(contract)

        # Journaliser la signature
        try:
            from src.services.logging_service import SentryLogger
            SentryLogger().log_contract_signature(contract, self.current_user)
        except Exception as e:
            print(f"Erreur lors du log de signature: {e}")

        return contract

    def delete_contract(self, contract_id: int) -> bool:
        """Supprimer un contrat"""
        contract = self.get_contract_by_id(contract_id)
        if not contract:
            raise ValidationError("Contrat non trouvé")

        # Seule la gestion peut supprimer des contrats
        if not self.current_user.is_gestion:
            raise AuthorizationError("Seule la gestion peut supprimer des contrats")

        # Vérifier qu'il n'y a pas d'événements associés
        if contract.events:
            raise ValidationError("Impossible de supprimer un contrat avec des événements associés")

        try:
            self.db.delete(contract)
            self.safe_commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erreur lors de la suppression: {e}")

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
