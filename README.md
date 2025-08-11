# OC_projet12 - Epic Events CRM

## Diagramme ERD (Entity-Relationship Diagram)

```mermaid
erDiagram
    User {
        int id PK
        string username
        string email
        string first_name
        string last_name
        string role
        string employee_number
        datetime created_at
        datetime updated_at
    }
    
    Client {
        int id PK
        string company_name
        string first_name
        string last_name
        string email
        string phone
        string mobile
        int sales_contact_id FK
        datetime created_at
        datetime updated_at
    }
    
    Contract {
        int id PK
        int client_id FK
        int sales_contact_id FK
        decimal total_amount
        decimal amount_due
        boolean is_signed
        datetime created_at
        datetime updated_at
    }
    
    Event {
        int id PK
        int contract_id FK
        string name
        int support_contact_id FK
        datetime event_date_start
        datetime event_date_end
        text location
        int attendees
        text notes
        datetime created_at
        datetime updated_at
    }

    %% Relations
    User ||--o{ Client : "sales_contact (COMMERCIAL)"
    User ||--o{ Contract : "sales_contact (COMMERCIAL)"
    User ||--o{ Event : "support_contact (SUPPORT)"
    Client ||--o{ Contract : "client"
    Contract ||--|| Event : "contract (OneToOne)"
```

## Relations entre les modèles

### Description des relations
- **User → Client** : Un commercial peut avoir plusieurs clients (ForeignKey)
- **User → Contract** : Un commercial peut gérer plusieurs contrats (ForeignKey)
- **User → Event** : Un support peut gérer plusieurs événements (ForeignKey)
- **Client → Contract** : Un client peut avoir plusieurs contrats (ForeignKey)
- **Contract → Event** : Un contrat a un seul événement (OneToOneField)

### Rôles utilisateurs
- **COMMERCIAL** : Gère les clients et leurs contrats
- **SUPPORT** : Gère les événements
- **GESTION** : Accès complet (création d'utilisateurs, contrats, assignation supports)

### Workflow métier
```
Commercial → Crée Client
     ↓
Gestion → Crée Contrat (lié au Client + Commercial)
     ↓
Commercial → Crée Event (si contrat signé)
     ↓
Gestion → Assigne Support à l'Event
```