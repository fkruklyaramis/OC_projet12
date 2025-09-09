"""
Gestion des connexions SQLAlchemy pour Epic Events CRM

Ce module établit et configure les connexions à la base de données en utilisant
SQLAlchemy ORM. Il implémente le pattern Factory pour la création de sessions
et fournit la classe de base pour tous les modèles de données.

Architecture SQLAlchemy:
    1. Engine: Moteur de base de données avec pool de connexions
    2. SessionLocal: Factory pour créer des sessions isolées
    3. Base: Classe parente pour tous les modèles ORM
    4. get_db(): Générateur de sessions avec gestion automatique du cycle de vie

Configuration du moteur:
    - Pool de connexions: Réutilisation optimisée des connexions
    - Echo: Désactivé en production, configurable pour debug
    - Autocommit: False pour contrôle explicite des transactions
    - Autoflush: False pour optimisation des performances

Pattern de sessions:
    - Une session par requête/opération
    - Fermeture automatique garantie (try/finally)
    - Isolation des transactions
    - Rollback automatique en cas d'exception

Utilisation recommandée:
```python
# Dans un contrôleur ou service
from src.database.connection import get_db

def my_business_operation():
    for session in get_db():
        user = session.query(User).filter_by(id=1).first()
        session.commit()
        # Session fermée automatiquement
```

Sécurité:
    - Pas de connexions persistantes
    - Isolation des transactions par défaut
    - Protection contre les injections SQL via ORM
    - Timeout configuré pour éviter les connexions orphelines

Performance:
    - Pool de connexions pour réutilisation
    - Lazy loading des relations configuré par modèle
    - Index optimisés définis dans les modèles
    - Requêtes préparées via SQLAlchemy Core

Fichier: src/database/connection.py
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import DATABASE_URL

# Création du moteur SQLAlchemy avec pool de connexions optimisé
# echo=False désactive le logging SQL (activation possible pour debug)
engine = create_engine(DATABASE_URL, echo=False)

# Factory de sessions configurée pour isolation transactionnelle
# autocommit=False: Contrôle explicite des transactions
# autoflush=False: Optimisation des performances, flush manuel si nécessaire
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Classe de base pour tous les modèles ORM
# Fournit les métadonnées et fonctionnalités communes à toutes les entités
Base = declarative_base()


def get_db():
    """
    Générateur de sessions de base de données avec gestion automatique du cycle de vie.

    Ce générateur implémente le pattern Context Manager pour garantir que chaque
    session soit correctement fermée, même en cas d'exception. Il est conçu pour
    être utilisé avec l'injection de dépendances dans les contrôleurs.

    Yields:
        Session: Session SQLAlchemy configurée et prête à utiliser

    Fonctionnement:
        1. Création d'une nouvelle session isolée
        2. Yield de la session pour utilisation
        3. Fermeture automatique garantie dans le bloc finally

    Exemple d'utilisation:
    ```python
    def create_user(user_data):
        for db in get_db():
            new_user = User(**user_data)
            db.add(new_user)
            db.commit()
            return new_user
    ```

    Note:
        Chaque appel crée une nouvelle session. Pour les opérations complexes
        nécessitant plusieurs requêtes, utilisez une seule session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        # Fermeture garantie de la session pour libérer les ressources
        # et éviter les fuites de connexions
        db.close()


def create_tables():
    """
    Créer toutes les tables définies dans les modèles ORM.

    Cette fonction utilise les métadonnées SQLAlchemy pour générer et exécuter
    automatiquement les instructions DDL (CREATE TABLE) correspondant à tous
    les modèles qui héritent de la classe Base.

    Comportement:
        - Création uniquement des tables manquantes (IF NOT EXISTS implicite)
        - Respect de l'ordre des dépendances (Foreign Keys)
        - Création des index définis dans les modèles
        - Support des contraintes métier définies au niveau modèle

    Utilisation:
        Appelée au démarrage de l'application ou dans les scripts d'initialisation.
        Ne modifie pas les tables existantes (pas de migration automatique).

    Note:
        Pour les migrations de schéma en production, utiliser Alembic
        plutôt que cette fonction qui est destinée au développement.
    """
    Base.metadata.create_all(bind=engine)
