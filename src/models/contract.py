"""
Modèle Contract - Gestion des contrats commerciaux Epic Events CRM

Ce module définit le modèle pour les contrats commerciaux, élément central
du processus métier Epic Events. Il gère le cycle de vie complet des accords
commerciaux depuis la négociation jusqu'à la facturation et l'exécution.

Architecture financière:
    - Montants en précision décimale pour exactitude comptable
    - Suivi du solde dû pour gestion de trésorerie
    - États de contrat stricts pour contrôle workflow
    - Audit automatique des modifications financières

Workflow contractuel:
    1. DRAFT: Négociation en cours, montants prévisionnels
    2. SIGNED: Contrat signé, engagement ferme client
    3. CANCELLED: Annulation, aucun événement possible

Contraintes métier:
    - Seuls les commerciaux peuvent créer/modifier des contrats
    - Contrats signés requis pour création d'événements
    - Montant dû ≤ montant total (cohérence financière)
    - Signature et statut cohérents (intégrité des données)

Relations critiques:
    - Lié à un client unique (traçabilité commerciale)
    - Assigné à un commercial (responsabilité)
    - Génère des événements (exécution)

Fichier: src/models/contract.py
"""
from sqlalchemy import Column, Integer, DateTime, Numeric, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database.connection import Base
import enum


class ContractStatus(enum.Enum):
    """
    Énumération des statuts de contrat avec workflow métier strict.

    Cette énumération définit les états possibles d'un contrat dans le
    système Epic Events. Chaque statut détermine les actions autorisées
    et les règles métier applicables au contrat.

    Statuts et significations:
        DRAFT: Contrat en cours de négociation
            - Modifications libres des montants et conditions
            - Aucun événement ne peut être créé
            - Peut être annulé sans impact financier
            - État par défaut à la création

        SIGNED: Contrat signé et engageant
            - Montants figés, modifications limitées
            - Création d'événements autorisée
            - Facturation possible selon termes
            - Audit renforcé des modifications

        CANCELLED: Contrat annulé
            - Aucune modification possible
            - Événements existants suspendus
            - État terminal, pas de retour possible
            - Conservation pour historique et audit

    Transitions autorisées:
        DRAFT → SIGNED (signature)
        DRAFT → CANCELLED (abandon négociation)
        SIGNED → CANCELLED (résiliation exceptionnelle)
    """
    DRAFT = "draft"
    SIGNED = "signed"
    CANCELLED = "cancelled"


class Contract(Base):
    """
    Modèle Contract - Représentation des accords commerciaux.

    Cette classe modélise les contrats commerciaux d'Epic Events avec toute
    la logique financière et métier nécessaire au suivi des engagements
    client. Elle assure la cohérence entre négociation, signature et
    exécution des prestations événementielles.

    Responsabilités financières:
        - Suivi précis des montants contractuels
        - Calcul automatique des soldes dus
        - Validation des règles de facturation
        - Audit des modifications financières

    Responsabilités métier:
        - Contrôle du workflow de signature
        - Autorisation de création d'événements
        - Traçabilité des responsabilités commerciales
        - Interface avec les systèmes comptables

    Contraintes d'intégrité:
        - amount_due ≤ total_amount (cohérence financière)
        - signed = True ⟺ status = SIGNED (cohérence d'état)
        - Events possibles uniquement si signed = True
        - Commercial assigné doit exister et être actif

    Attributes:
        id: Identifiant unique du contrat (clé primaire)
        total_amount: Montant total HT en euros (précision 2 décimales)
        amount_due: Montant restant dû en euros (précision 2 décimales)
        status: Statut actuel du contrat (DRAFT/SIGNED/CANCELLED)
        signed: Indicateur booléen de signature effective
        client_id: Référence vers le client (clé étrangère)
        commercial_contact_id: Référence vers le commercial (clé étrangère)
        created_at: Date de création automatique
        updated_at: Date de dernière modification automatique
        signed_at: Date de signature (nullable, renseignée à la signature)

    Relations:
        client: Client bénéficiaire du contrat
        commercial_contact: Commercial responsable de la négociation
        events: Liste des événements générés par ce contrat
    """
    __tablename__ = "contracts"

    # Identifiant unique du contrat
    id = Column(Integer, primary_key=True, index=True)

    # Données financières avec précision décimale pour exactitude comptable
    total_amount = Column(Numeric(10, 2), nullable=False)  # Montant total HT
    amount_due = Column(Numeric(10, 2), nullable=False)    # Solde restant dû

    # Workflow et statut contractuel
    status = Column(Enum(ContractStatus), default=ContractStatus.DRAFT, nullable=False)
    signed = Column(Boolean, default=False, nullable=False)

    # Relations métier obligatoires pour traçabilité
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    commercial_contact_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Audit automatique des modifications avec timezone
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    signed_at = Column(DateTime(timezone=True), nullable=True)  # Renseigné à la signature

    # Relations ORM bidirectionnelles pour navigation efficace
    client = relationship("Client", back_populates="contracts")
    commercial_contact = relationship("User", foreign_keys=[commercial_contact_id])
    events = relationship("Event", back_populates="contract")

    def __repr__(self):
        """Représentation technique pour debugging et logs système."""
        return f"<Contract(id={self.id}, client_id={self.client_id}, " \
               f"amount={self.total_amount}, status={self.status.value})>"

    @property
    def is_signed(self) -> bool:
        """
        Vérifier si le contrat est effectivement signé et valide.

        Cette propriété vérifie la cohérence entre l'indicateur de signature
        et le statut contractuel pour s'assurer que le contrat est dans un
        état valide pour la création d'événements.

        Returns:
            bool: True si le contrat est signé ET en statut SIGNED

        Utilisation métier:
            - Autorisation de création d'événements
            - Validation des workflows de facturation
            - Contrôles d'intégrité avant opérations critiques
            - Audit de cohérence des données contractuelles
        """
        return self.signed and self.status == ContractStatus.SIGNED

    @property
    def is_fully_paid(self) -> bool:
        """
        Vérifier si le contrat est entièrement payé.

        Cette propriété détermine si le client a soldé intégralement
        ses obligations financières pour ce contrat, information
        critique pour la gestion de trésorerie et le suivi client.

        Returns:
            bool: True si montant dû ≤ 0 (contrat soldé)

        Utilisation métier:
            - Gestion des relances client
            - Calcul des créances en cours
            - Reporting financier
            - Validation avant clôture de contrat
            - Segmentation clients par solvabilité
        """
        return self.amount_due <= 0

    @property
    def remaining_amount(self) -> float:
        """
        Obtenir le montant restant dû en format float pour calculs.

        Cette propriété convertit le montant Decimal en float pour
        faciliter les calculs et intégrations avec d'autres systèmes
        tout en préservant la précision des données financières.

        Returns:
            float: Montant restant dû en euros

        Utilisation métier:
            - Calculs de reporting financier
            - Intégration avec systèmes comptables
            - Affichage dans interfaces utilisateur
            - APIs et échanges de données
            - Calculs de commissions commerciales
        """
        return float(self.amount_due)
