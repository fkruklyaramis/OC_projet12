"""
Package database pour Epic Events CRM

Ce package centralise toute la logique de gestion des données et des connexions
pour l'application Epic Events. Il fournit une architecture de persistance
robuste et sécurisée basée sur SQLAlchemy ORM.

Architecture de la couche données:
    - config.py: Configuration centralisée des paramètres de base de données
    - connection.py: Gestion des connexions SQLAlchemy et sessions
    - init_db.py: Initialisation et peuplement avec données d'exemple

Responsabilités du package:
    1. Configuration: Variables d'environnement et paramètres de connexion
    2. Connexions: Pool de connexions SQLAlchemy optimisé
    3. Sessions: Gestionnaire de sessions avec gestion automatique des transactions
    4. Initialisation: Création des tables et données de démonstration
    5. Migration: Structure pour évolutions futures du schéma

Patterns implémentés:
    - Repository Pattern: Abstraction de l'accès aux données
    - Unit of Work: Gestion cohérente des transactions
    - Factory Pattern: Création standardisée des sessions
    - Dependency Injection: Injection des sessions dans les contrôleurs

Points d'intégration:
    - Modèles ORM: Définition des entités métier (User, Client, Contract, Event)
    - Contrôleurs: Injection des sessions pour opérations CRUD
    - Services: Accès transactionnel pour logique métier complexe
    - Tests: Sessions isolées pour tests unitaires et d'intégration

Sécurité et performance:
    - Pool de connexions configuré pour haute disponibilité
    - Transactions automatiques avec rollback en cas d'erreur
    - Timeout configurable pour éviter les connexions orphelines
    - Logs détaillés pour monitoring et debug (mode développement)

Configuration environnements:
    - Développement: SQLite local avec echo SQL activé
    - Test: Base temporaire isolée par test
    - Production: PostgreSQL avec optimisations performance

Utilisation:
```python
# Import de la session factory
from src.database.connection import get_db

# Utilisation dans un contrôleur
def my_controller_method():
    with get_db() as session:
        # Opérations de base de données
        pass
```

Fichier: src/database/__init__.py
"""
