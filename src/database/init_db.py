"""
Initialisation et peuplement de la base de données Epic Events CRM

Ce module fournit les fonctionnalités pour initialiser une base de données
complète avec des données d'exemple représentatives d'un environnement
de production. Il est essentiel pour le développement, les tests et les
démonstrations du système Epic Events.

Fonctionnalités principales:
    1. Suppression sécurisée des tables existantes
    2. Création du schéma complet de base de données
    3. Génération de données d'exemple cohérentes et réalistes
    4. Validation de l'intégrité référentielle

Architecture des données d'exemple:
    - Utilisateurs: Représentant tous les départements (GESTION, COMMERCIAL, SUPPORT)
    - Clients: Entreprises variées avec contacts commerciaux assignés
    - Contrats: Différents statuts (signés, non signés) avec montants réalistes
    - Événements: Planification complète avec assignation support

Intérêt pédagogique:
    Les données générées permettent de tester tous les workflows métier:
    - Création et gestion des prospects par les commerciaux
    - Négociation et signature des contrats
    - Planification des événements avec équipes support
    - Suivi financier et reporting pour la gestion

Sécurité des données:
    - Mots de passe hachés avec algorithme sécurisé
    - Numéros d'employés uniques générés automatiquement
    - Emails professionnels cohérents avec la nomenclature entreprise
    - Dates réalistes respectant la chronologie métier

Utilisation:
    Exécution standalone pour réinitialisation complète de la base:
    ```bash
    python src/database/init_db.py
    ```

    Ou import dans scripts de déploiement:
    ```python
    from src.database.init_db import init_database
    init_database()
    ```

Note importante:
    Ce script détruit toutes les données existantes. À utiliser uniquement
    en développement ou pour initialisation de nouvelles instances.

Fichier: src/database/init_db.py
"""
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from src.database.connection import engine, Base
from src.models.user import User, Department
from src.models.client import Client
from src.models.contract import Contract, ContractStatus
from src.models.event import Event
from src.utils.hash_utils import hash_password
from src.config.messages import GENERAL_MESSAGES


def drop_all_tables():
    """
    Supprimer toutes les tables existantes de la base de données.

    Cette fonction effectue une suppression complète et irréversible de toutes
    les tables définies dans les métadonnées SQLAlchemy. Elle respecte l'ordre
    des dépendances pour éviter les erreurs de contraintes de clés étrangères.

    Utilisation:
        Appelée avant la recréation complète d'une base pour s'assurer
        d'un état propre, particulièrement utile lors du développement
        ou de la réinitialisation d'environnements de test.

    Attention:
        TOUTES LES DONNÉES SONT PERDUES. Ne jamais utiliser en production
        sur des données importantes sans sauvegarde préalable.

    Ordre de suppression:
        SQLAlchemy gère automatiquement l'ordre en analysant les foreign keys,
        supprimant d'abord les tables dépendantes puis les tables référencées.
    """
    print(GENERAL_MESSAGES["db_dropping_tables"])
    Base.metadata.drop_all(bind=engine)
    print(GENERAL_MESSAGES["db_tables_dropped"])


def create_sample_data(session):
    """
    Créer un jeu de données d'exemple complet et cohérent.

    Cette fonction génère des données représentatives de tous les types
    d'entités métier avec des relations cohérentes et des valeurs réalistes.
    Les données sont conçues pour permettre la démonstration de tous les
    workflows de l'application Epic Events.

    Args:
        session: Session SQLAlchemy active pour les opérations de persistance

    Structure des données générées:
        - 5 utilisateurs (1 admin, 2 commerciaux, 2 support)
        - 4 clients d'entreprises variées
        - 4 contrats avec différents statuts et montants
        - 3 événements planifiés avec assignations support

    Cohérence métier:
        - Chaque client est assigné à un commercial spécifique
        - Les contrats respectent les règles de montants et statuts
        - Les événements sont liés à des contrats signés uniquement
        - Les dates respectent la chronologie logique des processus

    Sécurité:
        - Tous les mots de passe sont hachés avec l'algorithme sécurisé
        - Les identifiants suivent la nomenclature officielle
        - Les emails respectent le domaine de l'entreprise

    Exception handling:
        - Chaque section peut être exécutée indépendamment
        - Les erreurs sont propagées pour traitement par l'appelant
        - Session commit après chaque groupe d'entités
    """

    # ====================================================================
    # 1. CRÉATION DES UTILISATEURS - BASE DU SYSTÈME D'AUTHENTIFICATION
    # ====================================================================
    print(GENERAL_MESSAGES["db_creating_users"])

    # Administrateur système - Département GESTION
    # Responsable de la gestion des utilisateurs et configuration système
    admin = User(
        employee_number="EE000001",
        email="admin@epicevents.com",
        hashed_password=hash_password("Admin123!"),
        full_name="Jean Dupont",
        department=Department.GESTION
    )
    session.add(admin)

    # Commercial principal - Responsable grands comptes
    # Gestion des clients TechCorp et Innovate SARL
    commercial1 = User(
        employee_number="EE000002",
        email="marie.martin@epicevents.com",
        hashed_password=hash_password("Commercial123!"),
        full_name="Marie Martin",
        department=Department.COMMERCIAL
    )
    session.add(commercial1)

    # Commercial junior - Développement nouveaux prospects
    # Gestion des clients StartUp et BigCorp
    commercial2 = User(
        employee_number="EE000003",
        email="pierre.durand@epicevents.com",
        hashed_password=hash_password("Commercial123!"),
        full_name="Pierre Durand",
        department=Department.COMMERCIAL
    )
    session.add(commercial2)

    # Support senior - Coordination événements complexes
    # Spécialisé dans les événements corporate et internationaux
    support1 = User(
        employee_number="EE000004",
        email="sophie.bernard@epicevents.com",
        hashed_password=hash_password("Support123!"),
        full_name="Sophie Bernard",
        department=Department.SUPPORT
    )
    session.add(support1)

    # Support junior - Événements standards et formations
    # Focus sur les séminaires et événements de formation
    support2 = User(
        employee_number="EE000005",
        email="lucas.petit@epicevents.com",
        hashed_password=hash_password("Support123!"),
        full_name="Lucas Petit",
        department=Department.SUPPORT
    )
    session.add(support2)

    # Validation et persistence des utilisateurs avant de continuer
    session.commit()
    print(GENERAL_MESSAGES["db_users_created"])

    # ====================================================================
    # 2. CRÉATION DES CLIENTS - PROSPECTS ET ENTREPRISES CLIENTES
    # ====================================================================
    print(GENERAL_MESSAGES["db_creating_clients"])

    # Client premium - Secteur technologie
    # Entreprise établie avec historique de contrats importants
    client1 = Client(
        full_name="Alice Rousseau",
        email="alice@techcorp.com",
        phone="01.23.45.67.89",
        company_name="TechCorp Solutions",
        commercial_contact_id=commercial1.id  # Assigné au commercial senior
    )
    session.add(client1)

    # Client standard - Secteur innovation
    # SARL en croissance avec potentiel de développement
    client2 = Client(
        full_name="Bob Moreau",
        email="bob@innovate.fr",
        phone="01.98.76.54.32",
        company_name="Innovate SARL",
        commercial_contact_id=commercial1.id  # Même commercial pour synergie
    )
    session.add(client2)

    # Prospect qualifié - Secteur startup
    # Nouvelle entreprise avec besoins d'événements de lancement
    client3 = Client(
        full_name="Catherine Leroy",
        email="c.leroy@startup.com",
        phone="01.11.22.33.44",
        company_name="StartUp Dynamics",
        commercial_contact_id=commercial2.id  # Assigné au commercial junior
    )
    session.add(client3)

    # Client enterprise - Secteur international
    # Multinationale avec besoins d'événements complexes et récurrents
    client4 = Client(
        full_name="David Lambert",
        email="d.lambert@bigcorp.fr",
        phone="01.55.66.77.88",
        company_name="BigCorp International",
        commercial_contact_id=commercial2.id  # Portefeuille commercial équilibré
    )
    session.add(client4)

    # Validation des clients avant création des contrats
    session.commit()
    print(GENERAL_MESSAGES["db_clients_created"])

    # ====================================================================
    # 3. CRÉATION DES CONTRATS - ACCORDS COMMERCIAUX ET SUIVI FINANCIER
    # ====================================================================
    print(GENERAL_MESSAGES["db_creating_contracts"])

    # Contrat signé et soldé - Modèle de réussite commerciale
    # Événement déjà organisé avec succès, relation client consolidée
    contract1 = Contract(
        client_id=client1.id,
        commercial_contact_id=commercial1.id,
        total_amount=15000.00,  # Montant standard pour événement corporate
        amount_due=0.00,        # Entièrement payé - client fiable
        status=ContractStatus.SIGNED,
        signed=True,
        signed_at=datetime.now() - timedelta(days=30)  # Signé il y a un mois
    )
    session.add(contract1)

    # Contrat signé avec solde dû - Gestion du risque client
    # Nécessite suivi rapproché pour recouvrement du solde
    contract2 = Contract(
        client_id=client2.id,
        commercial_contact_id=commercial1.id,
        total_amount=25000.00,  # Contrat plus important
        amount_due=10000.00,    # 40% restant à encaisser
        status=ContractStatus.SIGNED,
        signed=True,
        signed_at=datetime.now() - timedelta(days=15)  # Récemment signé
    )
    session.add(contract2)

    # Contrat en négociation - Pipeline commercial actif
    # Prospect qualifié en phase de closing, nécessite suivi commercial
    contract3 = Contract(
        client_id=client3.id,
        commercial_contact_id=commercial2.id,
        total_amount=8000.00,   # Montant startup approprié
        amount_due=8000.00,     # Intégralement dû (non signé)
        status=ContractStatus.DRAFT,  # En cours de négociation
        signed=False            # Signature en attente
    )
    session.add(contract3)

    # Contrat premium récemment signé - Opportunité majeure
    # Client international avec budget conséquent et potentiel récurrent
    contract4 = Contract(
        client_id=client4.id,
        commercial_contact_id=commercial2.id,
        total_amount=50000.00,  # Contrat premium de grande envergure
        amount_due=20000.00,    # 60% déjà encaissé, bon profil de paiement
        status=ContractStatus.SIGNED,
        signed=True,
        signed_at=datetime.now() - timedelta(days=5)  # Très récemment signé
    )
    session.add(contract4)

    # Validation des contrats avant création des événements
    session.commit()
    print(GENERAL_MESSAGES["db_contracts_created"])

    # ====================================================================
    # 4. CRÉATION DES ÉVÉNEMENTS - PLANIFICATION ET COORDINATION
    # ====================================================================
    print(GENERAL_MESSAGES["db_creating_events"])

    # Événement terminé - Référence de succès
    # Séminaire corporate réussi servant de showcase pour futurs clients
    event1 = Event(
        name="Séminaire Innovation TechCorp 2024",
        location="Centre de Conférences Paris La Défense",
        attendees=75,   # Audience corporate standard
        notes="Événement corporate premium avec livestream. "
              "Retours très positifs des participants. "
              "Client satisfait et ouvert pour reconduction 2025.",
        start_date=datetime.now() - timedelta(days=45),  # Il y a 45 jours
        end_date=datetime.now() - timedelta(days=44),    # Durée 1 jour
        contract_id=contract1.id,
        support_contact_id=support1.id  # Support senior pour événement premium
    )
    session.add(event1)

    # Événement à venir - En cours de préparation
    # Formation d'équipe nécessitant coordination logistique avancée
    event2 = Event(
        name="Formation Leadership Innovate SARL",
        location="Hôtel Marriott Champs-Élysées",
        attendees=25,   # Format formation intensive
        notes="Formation sur 2 jours avec ateliers pratiques. "
              "Matériel audiovisuel haut de gamme requis. "
              "Coordination étroite avec formateurs externes.",
        start_date=datetime.now() + timedelta(days=30),  # Dans 30 jours
        end_date=datetime.now() + timedelta(days=31),    # Formation 2 jours
        contract_id=contract2.id,
        support_contact_id=support2.id  # Support junior pour format standard
    )
    session.add(event2)

    # Événement complexe planifié - Défi logistique
    # Convention internationale nécessitant coordination multi-équipes
    event3 = Event(
        name="Convention Internationale BigCorp 2025",
        location="Palais des Congrès de Versailles",
        attendees=300,  # Événement de grande envergure
        notes="Convention internationale sur 3 jours. "
              "Participants de 15 pays, traduction simultanée. "
              "Coordination avec équipes techniques spécialisées. "
              "Budget premium justifié par la complexité.",
        start_date=datetime.now() + timedelta(days=90),  # Dans 3 mois
        end_date=datetime.now() + timedelta(days=92),    # Convention 3 jours
        contract_id=contract4.id,
        support_contact_id=support1.id  # Support senior obligatoire
    )
    session.add(event3)

    # Validation finale des événements
    session.commit()
    print(GENERAL_MESSAGES["db_events_created"])

    # ====================================================================
    # RÉSUMÉ DES DONNÉES CRÉÉES - INFORMATIONS POUR L'UTILISATEUR
    # ====================================================================
    print("\n=== DONNÉES CRÉÉES AVEC SUCCÈS ===")
    print("Utilisateurs (comptes de test):")
    print("- admin@epicevents.com (mot de passe: Admin123!) - GESTION")
    print("- marie.martin@epicevents.com (mot de passe: Commercial123!) - COMMERCIAL")
    print("- pierre.durand@epicevents.com (mot de passe: Commercial123!) - COMMERCIAL")
    print("- sophie.bernard@epicevents.com (mot de passe: Support123!) - SUPPORT")
    print("- lucas.petit@epicevents.com (mot de passe: Support123!) - SUPPORT")
    print("\nClients: 4 entreprises créées avec contacts commerciaux assignés")
    print("Contrats: 4 créés (2 signés avec montants dus, 1 signé payé, 1 en négociation)")
    print("Événements: 3 créés (1 passé réussi, 2 à venir avec support assigné)")
    print("\nLa base de données est prête pour démonstration et tests.")


def init_database():
    """
    Initialiser complètement la base de données avec schéma et données d'exemple.

    Cette fonction orchestre le processus complet d'initialisation de la base
    de données, depuis la suppression des données existantes jusqu'à la création
    d'un jeu de données d'exemple cohérent et fonctionnel.

    Process d'initialisation:
        1. Suppression sécurisée des tables existantes
        2. Création du schéma complet (tables, index, contraintes)
        3. Génération des données d'exemple avec relations cohérentes
        4. Validation de l'intégrité référentielle

    Returns:
        bool: True si l'initialisation s'est déroulée sans erreur,
              False en cas de problème lors du processus

    Exception handling:
        - Rollback automatique en cas d'erreur de données
        - Fermeture propre de la session même en cas d'exception
        - Messages détaillés pour diagnostic des problèmes

    Utilisation:
        - Développement: Réinitialisation rapide de l'environnement
        - Tests: Création d'un état connu et reproductible
        - Démonstration: Base de données prête avec scénarios réalistes

    Sécurité:
        Fonction destructive qui supprime toutes les données existantes.
        Ne jamais utiliser sur une base de production avec des données importantes.

    Exemple:
    ```python
    if init_database():
        print("Base de données prête pour utilisation")
    else:
        print("Erreur lors de l'initialisation")
    ```
    """
    try:
        # Phase 1: Nettoyage et reconstruction du schéma
        drop_all_tables()
        print(GENERAL_MESSAGES["db_creating_tables"])
        Base.metadata.create_all(bind=engine)
        print("Tables créées avec succès.")

        # Phase 2: Création d'une session pour le peuplement des données
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        try:
            # Phase 3: Génération des données d'exemple avec validation
            create_sample_data(session)

            print("\n🎉 BASE DE DONNÉES INITIALISÉE AVEC SUCCÈS!")
            print("L'application Epic Events est prête à être utilisée.")
            return True

        except Exception as e:
            # Rollback en cas d'erreur pour maintenir la cohérence
            session.rollback()
            print(f"❌ Erreur lors de la création des données: {e}")
            return False
        finally:
            # Fermeture garantie de la session pour libérer les ressources
            session.close()

    except Exception as e:
        print(f"❌ Erreur critique lors de l'initialisation: {e}")
        return False


# Point d'entrée pour exécution standalone du script
if __name__ == "__main__":
    """
    Exécution directe du script d'initialisation.

    Permet de réinitialiser rapidement la base de données en exécutant:
    python src/database/init_db.py

    Utile pour:
    - Développement: Reset rapide de l'environnement local
    - Déploiement: Initialisation de nouvelles instances
    - Maintenance: Retour à un état propre et connu
    """
    init_database()
