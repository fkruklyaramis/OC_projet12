"""
Modèle Event - Gestion des événements Epic Events CRM

Ce module définit le modèle pour la planification et coordination des événements,
aboutissement du processus commercial Epic Events. Il représente la phase
d'exécution où les contrats signés se concrétisent en prestations événementielles.

Architecture opérationnelle:
    - Dépendance obligatoire sur contrat signé (contrainte métier)
    - Assignation optionnelle d'équipe support (flexibilité planning)
    - Gestion timezone-aware pour événements internationaux
    - Calculs automatiques de durée et métriques

Workflow événementiel:
    1. Création: Basée sur contrat signé uniquement
    2. Planification: Dates, lieu, audience définis
    3. Assignation: Support technique assigné selon complexité
    4. Exécution: Coordination temps réel jour J
    5. Clôture: Feedback client et bilan opérationnel

Contraintes opérationnelles:
    - Contract_id obligatoire vers contrat SIGNED uniquement
    - Dates cohérentes (start_date ≤ end_date)
    - Support assigné doit être département SUPPORT
    - Lieu et capacité selon type d'événement

Relations transversales:
    - Lié à un contrat unique (traçabilité financière)
    - Client accessible via contrat (relation transitive)
    - Support assigné pour coordination technique

Fichier: src/models/event.py
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database.connection import Base


class Event(Base):
    """
    Modèle Event - Représentation des événements organisés par Epic Events.

    Cette classe modélise les événements depuis leur planification jusqu'à
    leur exécution. Elle constitue l'aboutissement du processus commercial
    et le point de coordination de toutes les équipes (commercial, support,
    prestataires externes).

    Responsabilités opérationnelles:
        - Planification détaillée (dates, lieu, capacité)
        - Coordination des équipes internes et externes
        - Suivi en temps réel de l'exécution
        - Interface avec les systèmes de facturation
        - Collecte du feedback client post-événement

    Responsabilités métier:
        - Validation des prérequis contractuels
        - Respect des contraintes temporelles et logistiques
        - Assignation des ressources humaines et matérielles
        - Reporting de performance et satisfaction client

    Contraintes opérationnelles:
        - Création possible uniquement sur contrat SIGNED
        - start_date ≤ end_date (cohérence temporelle)
        - support_contact doit être département SUPPORT si assigné
        - attendees > 0 (événement doit avoir une audience)
        - location non vide (lieu physique ou virtuel obligatoire)

    Types d'événements supportés:
        - Conférences corporate (50-500 participants)
        - Séminaires formation (10-100 participants)
        - Événements networking (20-200 participants)
        - Conventions internationales (100-1000+ participants)
        - Workshops spécialisés (5-50 participants)

    Attributes:
        id: Identifiant unique de l'événement (clé primaire)
        name: Nom commercial de l'événement
        location: Lieu de l'événement (adresse complète ou plateforme virtuelle)
        attendees: Nombre de participants prévus
        notes: Notes techniques et logistiques (format libre)
        start_date: Date et heure de début (timezone-aware)
        end_date: Date et heure de fin (timezone-aware)
        contract_id: Référence vers le contrat source (clé étrangère obligatoire)
        support_contact_id: Référence vers support assigné (clé étrangère optionnelle)
        created_at: Date de création automatique
        updated_at: Date de dernière modification automatique

    Relations:
        contract: Contrat commercial source de l'événement
        support_contact: Membre de l'équipe support assigné
        client: Client final (accessible via contract.client)
        commercial_contact: Commercial responsable (accessible via contract.commercial_contact)
    """
    __tablename__ = "events"

    # Identifiant unique de l'événement
    id = Column(Integer, primary_key=True, index=True)

    # Informations descriptives de l'événement
    name = Column(String(255), nullable=False)                    # Nom commercial
    location = Column(String(500), nullable=False)               # Lieu détaillé
    attendees = Column(Integer, nullable=False)                  # Capacité prévue
    notes = Column(Text, nullable=True)                          # Notes techniques libres

    # Planification temporelle avec support timezone international
    start_date = Column(DateTime(timezone=True), nullable=False)  # Début événement
    end_date = Column(DateTime(timezone=True), nullable=False)    # Fin événement

    # Relations métier pour traçabilité et coordination
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)      # Contrat source obligatoire
    support_contact_id = Column(Integer, ForeignKey("users.id"), nullable=True)    # Support assigné optionnel

    # Audit automatique des modifications
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relations ORM pour navigation efficace dans le modèle de données
    contract = relationship("Contract", back_populates="events")
    support_contact = relationship("User", foreign_keys=[support_contact_id])

    def __repr__(self):
        """Représentation technique pour debugging et logs système."""
        return f"<Event(id={self.id}, name={self.name}, " \
               f"contract_id={self.contract_id}, support_id={self.support_contact_id})>"

    @property
    def duration_days(self) -> int:
        """
        Calculer la durée de l'événement en jours entiers.

        Cette propriété calcule automatiquement la durée de l'événement
        en jours calendaires pour faciliter la planification logistique
        et l'estimation des ressources nécessaires.

        Returns:
            int: Nombre de jours de l'événement (minimum 1)

        Utilisation opérationnelle:
            - Calcul des coûts de location de matériel
            - Planification des équipes support
            - Estimation des frais d'hébergement participants
            - Facturation selon durée contractuelle
            - Réservation des espaces et prestataires

        Note:
            Le calcul inclut les jours de début et fin, donc un événement
            d'une journée (même start_date et end_date) retourne 1.
        """
        return (self.end_date.date() - self.start_date.date()).days + 1

    @property
    def client(self):
        """
        Accéder au client final via la relation contractuelle.

        Cette propriété fournit un accès direct au client sans nécessiter
        de navigation manuelle via le contrat. Elle simplifie les requêtes
        et améliore la lisibilité du code métier.

        Returns:
            Client: Instance du client ou None si contrat invalide

        Utilisation métier:
            - Accès direct aux informations client depuis l'événement
            - Simplification des templates et vues
            - Raccourci pour notifications et communications client
            - Reporting consolidé événement-client
            - Interface utilisateur simplifiée

        Note:
            Retourne None si le contrat associé n'existe pas (situation
            exceptionnelle qui ne devrait pas se produire avec les
            contraintes d'intégrité référentielle).
        """
        return self.contract.client if self.contract else None
