"""
Initialisation centralisée des modèles Epic Events CRM

Ce module centralise l'importation et l'exposition de tous les modèles ORM
SQLAlchemy de l'application Epic Events. Il garantit l'ordre correct des imports
et évite les dépendances circulaires entre les modèles qui ont des relations
bidirectionnelles.

Architecture des relations métier:
    User (Commercial) ──1:N──→ Client ──1:N──→ Contract ──1:N──→ Event
           ↘                                                    ↗
             User (Support) ──────────1:N────────────────────→

Relations détaillées:
    - User (1) -> (N) Client (relation: commercial_contact)
      Un commercial gère plusieurs clients
    - User (1) -> (N) Contract (relation: commercial_contact)
      Un commercial suit plusieurs contrats
    - User (1) -> (N) Event (relation: support_contact)
      Un support coordonne plusieurs événements
    - Client (1) -> (N) Contract
      Un client peut avoir plusieurs contrats
    - Contract (1) -> (N) Event
      Un contrat peut générer plusieurs événements

Contraintes métier implémentées:
    1. Sécurité départementale:
       - Seuls les COMMERCIAL peuvent créer des clients
       - Seuls les GESTION peuvent gérer les utilisateurs
       - Les SUPPORT gèrent uniquement les événements assignés

    2. Intégrité financière:
       - Les contrats doivent être signés avant création d'événements
       - Les montants dus ne peuvent être négatifs
       - Le montant restant dû ≤ montant total du contrat

    3. Cohérence temporelle:
       - Date de signature ≤ date de création d'événement
       - Date de début ≤ date de fin pour les événements
       - Pas de modification des contrats avec événements en cours

Ordre d'import respecté:
    1. User + Department (base du système d'authentification)
    2. Client (dépend de User pour commercial_contact)
    3. Contract + ContractStatus (dépend de User et Client)
    4. Event (dépend de Contract et User pour support)

Utilisation:
    Ce module est le point d'entrée recommandé pour tous les imports
    de modèles dans l'application, garantissant la cohérence.

Fichier: src/models/models_init.py
"""

# Import des modèles dans l'ordre de dépendances pour éviter les erreurs circulaires
from .user import User, Department
from .client import Client
from .contract import Contract, ContractStatus
from .event import Event

# Export de tous les modèles et énumérations pour réutilisation
__all__ = [
    # Entités principales
    "User",
    "Client",
    "Contract",
    "Event",

    # Énumérations métier
    "Department",
    "ContractStatus"
]
