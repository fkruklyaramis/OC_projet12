"""
Configuration de la base de données pour Epic Events CRM

Ce module centralise tous les paramètres de configuration liés à la persistance
des données. Il gère les variables d'environnement et fournit des valeurs par
défaut sécurisées pour le développement.

Architecture de configuration:
    1. Variables d'environnement: Lecture sécurisée via python-dotenv
    2. Valeurs par défaut: Configuration de développement intégrée
    3. Sécurité: Clés secrètes et DSN Sentry externalisés
    4. Flexibilité: Support multi-environnements (dev/test/prod)

Paramètres configurables:
    - DATABASE_URL: URL de connexion à la base de données
    - SENTRY_DSN: Endpoint pour monitoring des erreurs
    - SECRET_KEY: Clé secrète pour chiffrement JWT et sessions

Formats DATABASE_URL supportés:
    - SQLite: sqlite:///./epic_events.db (développement)
    - PostgreSQL: postgresql://user:pass@host:port/db (production)
    - MySQL: mysql://user:pass@host:port/db (alternative)

Sécurité:
    - Aucune valeur sensible hardcodée dans le code
    - Variables d'environnement obligatoires en production
    - Valeurs par défaut uniquement pour développement local
    - Rotation des clés secrètes via variables d'environnement

Utilisation:
    Les valeurs sont importées directement par les autres modules
    du package database pour configurer SQLAlchemy et les services.

Exemple fichier .env:
```
DATABASE_URL=postgresql://epic:password@localhost:5432/epic_events
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
SECRET_KEY=your-super-secret-key-for-production
```

Fichier: src/database/config.py
"""
import os
from dotenv import load_dotenv

# Chargement des variables d'environnement depuis le fichier .env
# Ce fichier doit être créé localement et ajouté au .gitignore
load_dotenv()

# URL de connexion à la base de données
# Format: driver://username:password@host:port/database
# Défaut: SQLite local pour développement rapide sans installation
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./epic_events.db')

# DSN Sentry pour monitoring des erreurs en production
# Permet le suivi automatique des exceptions et performances
SENTRY_DSN = os.getenv('SENTRY_DSN')

# Clé secrète pour chiffrement JWT et protection CSRF
# ATTENTION: Doit être changée en production et gardée confidentielle
SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key-change-me')
