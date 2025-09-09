# Documentation Technique - Epic Events CRM

## 📚 Guide de Compréhension du Code

Cette documentation technique explique en détail l'architecture, les patterns utilisés et la structure du code pour faciliter la maintenance et l'évolution du projet.

## 🏗️ Architecture Générale

### Pattern MVC Implémenté

Epic Events CRM suit strictement le pattern MVC (Model-View-Controller) pour une séparation claire des responsabilités :

#### 📊 **Models (src/models/)**
Les modèles représentent la structure des données et les relations entre entités.

```python
# src/models/user.py
class User(Base):
    """
    Modèle utilisateur avec gestion des départements et permissions
    
    Fonctionnalités clés:
    - Stockage sécurisé des mots de passe (bcrypt)
    - Numéro d'employé unique auto-généré
    - Département définissant les permissions
    - Timestamps automatiques
    """
    __tablename__ = "users"
    
    # Clé primaire auto-incrémentée
    id = Column(Integer, primary_key=True)
    
    # Identifiants uniques avec index pour performances
    employee_number = Column(String(20), unique=True, index=True)
    email = Column(String(255), unique=True, index=True)
    
    # Informations utilisateur
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)  # Jamais en clair !
    
    # Département = permissions (enum pour sécurité)
    department = Column(Enum(Department), nullable=False, index=True)
```

#### 🎮 **Controllers (src/controllers/)**
Les contrôleurs contiennent la logique métier et orchestrent les opérations.

```python
# src/controllers/base_controller.py
class BaseController:
    """
    Contrôleur de base avec fonctionnalités communes
    
    Responsabilités:
    - Gestion des permissions et autorisations
    - Transactions sécurisées avec rollback automatique
    - Validation des données d'entrée
    - Gestion du contexte utilisateur
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session                    # Session SQLAlchemy
        self.current_user = None                # Utilisateur connecté
        self.permission_checker = PermissionChecker()  # Vérifications permissions
        self.validator = DataValidator()        # Validation des données
    
    def safe_commit(self):
        """
        Transaction sécurisée avec gestion d'erreurs
        Rollback automatique en cas de problème
        """
        try:
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()  # Annulation en cas d'erreur
            raise
```

#### 🖥️ **Views (src/views/)**
Les vues gèrent l'interface utilisateur (CLI dans notre cas).

```python
# src/views/base_view.py
class BaseView:
    """
    Vue de base avec utilitaires d'affichage
    
    Responsabilités:
    - Affichage formaté des données
    - Gestion des entrées utilisateur
    - Validation côté interface
    - Messages d'erreur utilisateur
    """
    
    def display_table(self, data, headers):
        """Affichage tabulaire avec rich pour la lisibilité"""
        
    def get_user_input(self, prompt, validator=None):
        """Saisie sécurisée avec validation"""
```

## 🔐 Système de Sécurité

### 1. Authentification JWT

```python
# src/utils/jwt_utils.py
class JWTManager:
    """
    Gestionnaire de tokens JWT pour l'authentification
    
    Sécurité:
    - Clé secrète unique stockée en variable d'environnement
    - Expiration automatique des tokens (24h)
    - Payload minimal (pas de données sensibles)
    - Validation systématique des tokens
    """
    
    def generate_token(self, user_id, email, department, employee_number):
        """
        Génère un token JWT sécurisé
        
        Payload contient uniquement:
        - user_id : Identifiant unique
        - email : Pour identification
        - department : Pour permissions
        - employee_number : Pour audit
        - exp : Date d'expiration
        """
        payload = {
            'user_id': user_id,
            'email': email,
            'department': department,
            'employee_number': employee_number,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
```

### 2. Système de Permissions

```python
# src/utils/auth_utils.py
class PermissionChecker:
    """
    Vérificateur de permissions basé sur les départements
    
    Matrice de permissions:
    - GESTION: Accès complet à toutes les fonctionnalités
    - COMMERCIAL: Clients et contrats de leurs clients
    - SUPPORT: Événements qui leur sont assignés
    """
    
    DEPARTMENT_PERMISSIONS = {
        Department.GESTION: [
            'create_user', 'read_user', 'update_user', 'delete_user',
            'create_client', 'read_client', 'update_client',
            'create_contract', 'read_contract', 'update_contract', 'sign_contract',
            'create_event', 'read_event', 'update_event', 'assign_event'
        ],
        Department.COMMERCIAL: [
            'create_client', 'read_client', 'update_client',
            'create_contract', 'read_contract', 'update_contract',
            'read_event'
        ],
        Department.SUPPORT: [
            'read_client', 'read_contract', 'read_event', 'update_event'
        ]
    }
```

### 3. Validation des Données

```python
# src/utils/validators.py
class DataValidator:
    """
    Validateur centralisé pour toutes les données d'entrée
    
    Sécurité:
    - Sanitisation des entrées
    - Validation des formats (email, téléphone, etc.)
    - Prévention des injections
    - Messages d'erreur clairs
    """
    
    def validate_email(self, email):
        """
        Validation email avec regex sécurisée
        - Format RFC 5322 complet
        - Longueur maximale
        - Caractères autorisés uniquement
        """
        if not email or len(email) > 254:
            raise ValidationError("Email invalide")
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValidationError("Format email invalide")
```

## 📊 Gestion de la Base de Données

### Configuration SQLAlchemy

```python
# src/database/connection.py
"""
Configuration centralisée de la base de données

Fonctionnalités:
- Pool de connexions pour les performances
- Gestion automatique des sessions
- Configuration différente par environnement
- Migrations avec Alembic (si nécessaire)
"""

engine = create_engine(
    DATABASE_URL,
    pool_size=10,           # Pool de connexions
    max_overflow=20,        # Connexions supplémentaires si besoin
    pool_pre_ping=True,     # Vérification de la connexion
    echo=False              # Logs SQL (True en développement)
)
```

### Modèles et Relations

```python
# Relations entre entités
class User(Base):
    # Un commercial peut avoir plusieurs clients
    clients = relationship("Client", back_populates="commercial_contact")

class Client(Base):
    # Un client appartient à un commercial
    commercial_contact = relationship("User", back_populates="clients")
    # Un client peut avoir plusieurs contrats
    contracts = relationship("Contract", back_populates="client")

class Contract(Base):
    # Un contrat appartient à un client
    client = relationship("Client", back_populates="contracts")
    # Un contrat peut avoir plusieurs événements
    events = relationship("Event", back_populates="contract")

class Event(Base):
    # Un événement appartient à un contrat
    contract = relationship("Contract", back_populates="events")
    # Un événement peut être assigné à un support
    support_contact = relationship("User", foreign_keys=[support_contact_id])
```

## 📈 Monitoring et Logging

### Service Sentry

```python
# src/services/logging_service.py
class SentryLogger:
    """
    Service de logging centralisé avec Sentry
    
    Fonctionnalités:
    - Logging automatique des événements critiques
    - Contexte utilisateur pour traçabilité
    - Gestion des erreurs sans interruption
    - Configuration par environnement
    """
    
    def log_authentication_attempt(self, email, success, ip_address=None):
        """
        Log des tentatives de connexion pour la sécurité
        
        Données loggées:
        - Email utilisé
        - Succès/échec
        - Adresse IP source
        - Timestamp précis
        
        Niveau: INFO (succès) / WARNING (échec)
        """
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("action", "authentication")
            scope.set_tag("success", str(success))
            scope.set_extra("auth_attempt", {
                "email": email,
                "success": success,
                "ip_address": ip_address or "unknown",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
```

## 🧪 Tests et Qualité

### Structure des Tests

```python
# tests/conftest.py
"""
Configuration globale des tests avec fixtures

Fonctionnalités:
- Base de données temporaire par test
- Données de test standardisées
- Isolation complète entre tests
- Nettoyage automatique
"""

@pytest.fixture(scope="function")
def db_session():
    """
    Crée une base de données temporaire pour chaque test
    Garantit l'isolation et la reproductibilité
    """
    # Fichier temporaire pour la base
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    
    # Création des tables
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    
    # Session de test
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session  # Fourni au test
    
    # Nettoyage après le test
    session.close()
    os.close(db_fd)
    os.unlink(db_path)
```

### Types de Tests

1. **Tests Unitaires** : Chaque composant isolément
2. **Tests d'Intégration** : Interaction entre composants
3. **Tests de Permissions** : Vérification des autorisations
4. **Tests de Sécurité** : Tentatives d'accès non autorisé

## 🔧 Bonnes Pratiques Implémentées

### 1. Séparation des Responsabilités
- Chaque classe a une responsabilité unique
- Services métier séparés de l'interface
- Utilitaires réutilisables centralisés

### 2. Gestion d'Erreurs
```python
try:
    # Opération risquée
    result = dangerous_operation()
except SpecificError as e:
    # Gestion spécifique
    logger.error(f"Erreur spécifique: {e}")
    raise
except Exception as e:
    # Gestion générale avec logging
    logger.exception("Erreur inattendue")
    raise SystemError("Erreur système")
```

### 3. Configuration par Environnement
```python
# Variables d'environnement pour la configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///epic_events.db')
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
SENTRY_DSN = os.getenv('SENTRY_DSN')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
```

### 4. Documentation Exhaustive
- Docstrings pour toutes les classes et méthodes
- Comments explicatifs pour la logique complexe
- Documentation d'architecture et d'usage
- Exemples d'utilisation

## 🚀 Extensions Possibles

### 1. API REST
```python
# Ajout d'une API REST avec FastAPI
from fastapi import FastAPI, Depends
from src.controllers.user_controller import UserController

app = FastAPI()

@app.get("/api/users")
def get_users(controller: UserController = Depends(get_controller)):
    return controller.get_all_users()
```

### 2. Interface Web
- Frontend React/Vue.js
- Authentication OAuth2
- Interface responsive

### 3. Fonctionnalités Avancées
- Notifications en temps réel
- Rapports et analytics
- Import/Export de données
- Audit trail complet

Cette documentation technique fournit une base solide pour comprendre, maintenir et étendre l'application Epic Events CRM.
