"""
Package services pour Epic Events CRM

Ce package contient tous les services métier de l'application Epic Events.
Il implémente la couche de logique métier entre les contrôleurs et les modèles,
fournissant des fonctionnalités transversales et spécialisées.

Architecture de services:
    - auth_service.py: Authentification, autorisation et gestion des sessions JWT
    - logging_service.py: Journalisation centralisée avec intégration Sentry

Responsabilités du package:
    1. Authentification: Gestion sécurisée des connexions utilisateur
    2. Autorisation: Contrôle d'accès basé sur les rôles et permissions
    3. Journalisation: Monitoring, audit et gestion des erreurs
    4. Intégrations: Services externes (Sentry pour monitoring)

Patterns implémentés:
    - Service Layer: Logique métier centralisée et réutilisable
    - Dependency Injection: Services injectés dans les contrôleurs
    - Observer Pattern: Logging automatique des événements critiques
    - Strategy Pattern: Différentes stratégies d'authentification

Points d'intégration:
    - Contrôleurs: Injection des services pour opérations métier
    - Modèles: Services utilisent les modèles pour persistance
    - Utils: Réutilisation des utilitaires spécialisés
    - Configuration: Services configurés via variables d'environnement

Sécurité et monitoring:
    - Authentification JWT sécurisée avec rotation des tokens
    - Logging automatique des tentatives d'authentification
    - Monitoring en temps réel des erreurs via Sentry
    - Audit trail complet des actions utilisateur

Configuration environnements:
    - Développement: Logging détaillé, Sentry optionnel
    - Test: Services mockés, pas de Sentry
    - Production: Sentry obligatoire, logging optimisé

Utilisation:
```python
# Import des services principaux
from src.services.auth_service import AuthenticationService
from src.services.logging_service import SentryLogger

# Utilisation dans un contrôleur
def my_controller_method(db_session):
    auth_service = AuthenticationService(db_session)
    user = auth_service.require_authentication()
```

Fichier: src/services/__init__.py
"""
