# Epic Events CRM

Application de gestion de la relation client (CRM) pour Epic Events, une entreprise d'organisation d'événements.

## Description

Epic Events CRM est une application en ligne de commande développée en Python qui permet de gérer :
- Les clients et leurs informations
- Les contrats et leur suivi
- Les événements organisés
- Les utilisateurs et leurs permissions par département

## Architecture

L'application suit une architecture modulaire avec séparation des responsabilités :

```
src/
├── database/          # Configuration et connexion base de données
├── models/           # Modèles de données SQLAlchemy
├── services/         # Logique métier
├── cli/              # Interface en ligne de commande
└── utils/            # Utilitaires (hachage, permissions)
```

## Diagramme Entity-Relationship (ERD)

```
                    ┌─────────────────────────────┐
                    │          USERS              │
                    ├─────────────────────────────┤
                    │ id (PK)                    │
                    │ email (UNIQUE)             │
                    │ hashed_password            │
                    │ full_name                  │
                    │ department (ENUM)          │
                    │ created_at                 │
                    │ updated_at                 │
                    └─────────────┬───────────────┘
                                  │
                                  │ 1:N (commercial_contact)
                                  │
    ┌─────────────────────────────▼─────────────────────────────┐
    │                    CLIENTS                                │
    ├───────────────────────────────────────────────────────────┤
    │ id (PK)                                                  │
    │ full_name                                                │
    │ email (UNIQUE)                                           │
    │ phone                                                    │
    │ company_name                                             │
    │ commercial_contact_id (FK → users.id)                   │
    │ created_at                                               │
    │ updated_at                                               │
    └─────────────────────────────┬─────────────────────────────┘
                                  │
                                  │ 1:N
                                  │
    ┌─────────────────────────────▼─────────────────────────────┐
    │                  CONTRACTS                               │
    ├───────────────────────────────────────────────────────────┤
    │ id (PK)                                                  │
    │ client_id (FK → clients.id)                             │
    │ commercial_contact_id (FK → users.id)                   │
    │ total_amount (DECIMAL)                                   │
    │ remaining_amount (DECIMAL)                               │
    │ is_signed (BOOLEAN)                                      │
    │ created_at                                               │
    │ updated_at                                               │
    └─────────────────────────────┬─────────────────────────────┘
                                  │
                                  │ 1:N
                                  │
    ┌─────────────────────────────▼─────────────────────────────┐
    │                   EVENTS                                 │
    ├───────────────────────────────────────────────────────────┤
    │ id (PK)                                                  │
    │ contract_id (FK → contracts.id)                         │
    │ name                                                     │
    │ support_contact_id (FK → users.id) [NULLABLE]           │
    │ start_date (DATETIME)                                    │
    │ end_date (DATETIME)                                      │
    │ location                                                 │
    │ attendees (INTEGER)                                      │
    │ notes (TEXT)                                             │
    │ created_at                                               │
    │ updated_at                                               │
    └───────────────────────────────────────────────────────────┘
                                  ▲
                                  │
                                  │ 1:N (support_contact)
                                  │
                    ┌─────────────┴───────────────┐
                    │          USERS              │
                    │    (Department: SUPPORT)    │
                    └─────────────────────────────┘
```

## Relations détaillées

### 1. User → Client (1:N - commercial_contact)
- **Cardinalité** : Un utilisateur commercial peut gérer plusieurs clients
- **Clé étrangère** : `clients.commercial_contact_id → users.id`
- **Contrainte** : Seuls les utilisateurs du département COMMERCIAL peuvent être assignés

### 2. User → Contract (1:N - commercial_contact)
- **Cardinalité** : Un utilisateur commercial peut gérer plusieurs contrats
- **Clé étrangère** : `contracts.commercial_contact_id → users.id`
- **Contrainte** : Le commercial du contrat doit être le même que celui du client

### 3. User → Event (1:N - support_contact)
- **Cardinalité** : Un utilisateur support peut être assigné à plusieurs événements
- **Clé étrangère** : `events.support_contact_id → users.id` (nullable)
- **Contrainte** : Seuls les utilisateurs du département SUPPORT peuvent être assignés

### 4. Client → Contract (1:N)
- **Cardinalité** : Un client peut avoir plusieurs contrats
- **Clé étrangère** : `contracts.client_id → clients.id`
- **Cascade** : DELETE CASCADE (suppression des contrats si client supprimé)

### 5. Contract → Event (1:N)
- **Cardinalité** : Un contrat peut avoir plusieurs événements
- **Clé étrangère** : `events.contract_id → contracts.id`
- **Contrainte métier** : Un événement ne peut être créé que si `contract.is_signed = True`

## Départements et permissions

### COMMERCIAL
- **Clients** : Créer, modifier ses clients assignés
- **Contrats** : Créer, modifier les contrats de ses clients
- **Événements** : Créer des événements pour les contrats signés de ses clients
- **Lecture** : Accès en lecture seule à tous les éléments

### SUPPORT
- **Événements** : Modifier les événements qui leur sont assignés
- **Lecture** : Accès en lecture seule à tous les éléments

### GESTION
- **Utilisateurs** : CRUD complet (Create, Read, Update, Delete)
- **Contrats** : CRUD complet
- **Événements** : Modifier (notamment pour assigner des supports)
- **Lecture** : Accès complet en lecture/écriture

## Contraintes métier

1. **Création client** : Seul un commercial peut créer un client (qui lui sera automatiquement assigné)
2. **Contrat signé** : Un événement ne peut être créé que pour un contrat signé
3. **Assignment support** : Seuls les utilisateurs du département SUPPORT peuvent être assignés aux événements
4. **Unicité email** : Les emails clients et utilisateurs sont uniques
5. **Intégrité référentielle** : Cascade de suppression appropriée entre les entités liées

## Installation

```bash
# Installer les dépendances
pip install -r requirements.txt

# Configurer l'environnement
cp .env.example .env

# Initialiser la base de données
python epicevents.py init
```

## Technologies utilisées

- **Python 3.9+**
- **SQLAlchemy** : ORM pour la gestion de base de données
- **SQLite** : Base de données (configurable)
- **Argon2** : Hachage sécurisé des mots de passe
- **Click** : Interface en ligne de commande
- **Sentry** : Monitoring et journalisation des erreurs
- **pytest** : Framework de tests

## Structure des données

### Énumérations

```python
class Department(enum.Enum):
    COMMERCIAL = "commercial"
    SUPPORT = "support" 
    GESTION = "gestion"
```

### Propriétés métier

Les modèles incluent des propriétés calculées utiles :

**Client :**
- `has_signed_contracts` : Vérifie si le client a des contrats signés
- `total_contract_amount` : Montant total des contrats signés

**Contract :**
- `is_fully_paid` : Vérifie si le contrat est entièrement payé
- `can_create_event` : Vérifie si un événement peut être créé
- `payment_percentage` : Pourcentage de paiement

**Event :**
- `is_upcoming` : Vérifie si l'événement est à venir
- `is_ongoing` : Vérifie si l'événement est en cours
- `is_past` : Vérifie si l'événement est terminé
- `duration_hours` : Durée de l'événement en heures

## Sécurité

- Mots de passe hachés avec Argon2
- Principe du moindre privilège appliqué
- Protection contre les injections SQL via SQLAlchemy ORM
- Variables d'environnement pour les informations sensibles
- Index sur les colonnes fréquemment utilisées pour les performances

## Base de données

Le fichier `epic_events.db` est créé automatiquement au premier lancement dans le répertoire racine du projet.




# 1. Initialiser la base avec des données d'exemple
python epicevents.py init

# 2. Se connecter en tant qu'admin
python epicevents.py login --email admin@epicevents.com
# Mot de passe: Admin123!

# 3. Vérifier le statut
python epicevents.py status

# 4. Tester les commandes clients
python epicevents.py client list

# 5. Tester les commandes contrats
python epicevents.py contract list
python epicevents.py contract unsigned
python epicevents.py contract unpaid
python epicevents.py contract view 1

# 6. Se connecter en tant que commercial
python epicevents.py logout
python epicevents.py login --email marie.martin@epicevents.com
# Mot de passe: Commercial123!

# 7. Voir ses propres clients et contrats
python epicevents.py client list --mine
python epicevents.py contract mine

# 8. Se connecter en tant que support
python epicevents.py logout
python epicevents.py login --email sophie.bernard@epicevents.com
# Mot de passe: Support123!

# Lister tous les événements (gestion seulement)
python epicevents.py event list

# Lister mes événements (support = assignés, commercial = mes contrats)
python epicevents.py event mine

# Événements à venir dans les 30 prochains jours
python epicevents.py event upcoming

# Événements à venir dans les 7 prochains jours
python epicevents.py event upcoming --days 7

# Événements sans support assigné
python epicevents.py event unassigned

# Voir les détails d'un événement
python epicevents.py event view 1

# Rechercher des événements
python epicevents.py event search

# Lister les utilisateurs
python epicevents.py user list
python epicevents.py user list --department commercial

# Créer un utilisateur
python epicevents.py user create

# Modifier un utilisateur
python epicevents.py user update 1

# Supprimer un utilisateur
python epicevents.py user delete 1

# Changer un mot de passe
python epicevents.py user password  # Son propre mot de passe
python epicevents.py user password 1  # Mot de passe d'un autre (gestion)

# Rechercher des utilisateurs
python epicevents.py user search

# Créer un client
python epicevents.py client create
python epicevents.py client create --commercial-id 2

# Modifier un client
python epicevents.py client update 1

# Supprimer un client (gestion uniquement)
python epicevents.py client delete 1

# Assigner un client (gestion uniquement)
python epicevents.py client assign 1 2
# Créer un contrat
python epicevents.py contract create 1  # Pour le client ID 1

# Modifier un contrat
python epicevents.py contract update 1

# Signer un contrat
python epicevents.py contract sign 1

# Créer un événement
python epicevents.py event create 1  # Pour le contrat ID 1

# Modifier un événement
python epicevents.py event update 1

# Assigner un support (gestion uniquement)
python epicevents.py event assign 1 3  # Événement 1 au support ID 3

/*
python epicevents.py user create
ajouter validation des email 

erreur ✗ Erreur: UserController.create_user() missing 4 required positional arguments: 'email', 'password', 'full_name', and 
'department'
*/