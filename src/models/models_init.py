"""
Initialisation des modèles pour Epic Events CRM

Relations entre les entités:
- User (1) -> (N) Client (relation: commercial_contact)
- User (1) -> (N) Contract (relation: commercial_contact)
- User (1) -> (N) Event (relation: support_contact)
- Client (1) -> (N) Contract
- Contract (1) -> (N) Event

Contraintes métier:
- Un client ne peut être créé que par un commercial
- Un contrat est toujours lié à un client et un commercial
- Un événement ne peut être créé que si le contrat est signé
- Un événement peut optionnellement avoir un contact support assigné
"""

from .user import User, Department
from .client import Client
from .contract import Contract
from .event import Event

__all__ = ["User", "Department", "Client", "Contract", "Event"]
