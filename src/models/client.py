"""
Modèle Client - Gestion de la relation client Epic Events CRM

Ce module définit le modèle pour la gestion des clients et prospects dans
l'application Epic Events. Il représente les entreprises clientes avec leurs
contacts désignés et maintient la relation avec l'équipe commerciale assignée.

Architecture relationnelle:
    - Chaque client est assigné à un commercial unique (relation N:1)
    - Un client peut avoir plusieurs contrats (relation 1:N)
    - Les contrats génèrent des événements (relation transitive)

Responsabilités métier:
    - Stockage des informations de contact client
    - Traçabilité de l'assignation commerciale
    - Calcul des métriques de valeur client
    - Audit automatique des modifications

Contraintes de sécurité:
    - Seuls les commerciaux peuvent créer/modifier des clients
    - Email unique pour éviter les doublons
    - Commercial assigné obligatoire pour traçabilité
    - Index optimisés pour recherches fréquentes

Métriques calculées:
    - Statut de signature des contrats
    - Valeur totale des contrats
    - Potentiel de développement commercial

Fichier: src/models/client.py
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database.connection import Base


class Client(Base):
    """
    Modèle Client - Représentation des entreprises clientes et prospects.

    Cette classe modélise les informations des clients d'Epic Events, depuis
    les prospects initiaux jusqu'aux clients fidèles avec historique de contrats.
    Elle maintient la relation essentielle avec l'équipe commerciale pour
    assurer la continuité du service et la responsabilité commerciale.

    Cycle de vie client:
        1. Prospect: Création par un commercial avec informations de base
        2. Qualifié: Ajout d'informations détaillées entreprise
        3. Client: Premier contrat signé et événement organisé
        4. Fidèle: Contrats récurrents et relation long terme

    Responsabilités:
        - Conservation des informations de contact actualisées
        - Liaison avec le commercial responsable du compte
        - Historique des contrats et événements
        - Métriques de valeur et potentiel commercial

    Contraintes métier:
        - Un client ne peut être créé que par un commercial
        - L'email doit être unique dans tout le système
        - Le commercial assigné ne peut être modifié qu'en interne
        - Toute modification est auditée automatiquement

    Attributes:
        id: Identifiant unique du client (clé primaire)
        full_name: Nom complet du contact principal
        email: Email professionnel unique (indexé pour recherches)
        phone: Numéro de téléphone direct du contact
        company_name: Raison sociale de l'entreprise (indexée)
        commercial_contact_id: ID du commercial assigné (clé étrangère)
        created_at: Date de création automatique
        updated_at: Date de dernière modification automatique

    Relations:
        commercial_contact: Commercial responsable du compte
        contracts: Liste des contrats associés au client
        events: Liste des événements (via les contrats)
    """
    __tablename__ = "clients"

    # Identifiant unique et informations de contact
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=False)

    # Informations entreprise (indexée pour recherches fréquentes)
    company_name = Column(String(255), nullable=False, index=True)

    # Relation obligatoire avec commercial pour traçabilité
    commercial_contact_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Audit automatique des modifications
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relations ORM bidirectionnelles pour navigation efficace
    commercial_contact = relationship("User", back_populates="clients")
    contracts = relationship("Contract", back_populates="client")

    def __repr__(self):
        """Représentation technique pour debugging et logs système."""
        return f"<Client(id={self.id}, name={self.full_name}, company={self.company_name})>"

    @property
    def has_signed_contracts(self) -> bool:
        """
        Vérifier si le client a des contrats signés.

        Cette propriété permet d'identifier rapidement les clients ayant
        franchi l'étape de signature, indicateur clé du passage de prospect
        à client effectif dans le pipeline commercial.

        Returns:
            bool: True si au moins un contrat est signé, False sinon

        Utilisation métier:
            - Segmentation de la base client (prospects vs clients)
            - Calcul du taux de conversion commercial
            - Priorisation des actions commerciales
            - Reporting de performance équipe commerciale
        """
        return any(contract.signed for contract in self.contracts)

    @property
    def total_contract_value(self) -> float:
        """
        Calculer la valeur totale de tous les contrats du client.

        Cette propriété calcule la somme de tous les montants contractuels
        pour évaluer la valeur totale du compte client. Elle inclut tous
        les contrats indépendamment de leur statut de signature.

        Returns:
            float: Montant total en euros de tous les contrats

        Utilisation métier:
            - Évaluation de la valeur client (Customer Lifetime Value)
            - Segmentation des comptes par valeur
            - Calcul des commissions commerciales
            - Reporting financier et prévisionnel
            - Priorisation des efforts de rétention client
        """
        return sum(float(contract.total_amount) for contract in self.contracts)
