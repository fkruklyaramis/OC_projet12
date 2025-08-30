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
    """Supprimer toutes les tables existantes"""
    print(GENERAL_MESSAGES["db_dropping_tables"])
    Base.metadata.drop_all(bind=engine)
    print(GENERAL_MESSAGES["db_tables_dropped"])


def create_sample_data(session):
    """Creer des donnees d'exemple pour tester l'application"""

    # 1. Creer des utilisateurs
    print(GENERAL_MESSAGES["db_creating_users"])

    # Admin/Gestion
    admin = User(
        employee_number="EE000001",
        email="admin@epicevents.com",
        hashed_password=hash_password("Admin123!"),
        full_name="Jean Dupont",
        department=Department.GESTION
    )
    session.add(admin)

    # Commercial 1
    commercial1 = User(
        employee_number="EE000002",
        email="marie.martin@epicevents.com",
        hashed_password=hash_password("Commercial123!"),
        full_name="Marie Martin",
        department=Department.COMMERCIAL
    )
    session.add(commercial1)

    # Commercial 2
    commercial2 = User(
        employee_number="EE000003",
        email="pierre.durand@epicevents.com",
        hashed_password=hash_password("Commercial123!"),
        full_name="Pierre Durand",
        department=Department.COMMERCIAL
    )
    session.add(commercial2)

    # Support 1
    support1 = User(
        employee_number="EE000004",
        email="sophie.bernard@epicevents.com",
        hashed_password=hash_password("Support123!"),
        full_name="Sophie Bernard",
        department=Department.SUPPORT
    )
    session.add(support1)

    # Support 2
    support2 = User(
        employee_number="EE000005",
        email="lucas.petit@epicevents.com",
        hashed_password=hash_password("Support123!"),
        full_name="Lucas Petit",
        department=Department.SUPPORT
    )
    session.add(support2)

    session.commit()
    print(GENERAL_MESSAGES["db_users_created"])

    # 2. Creer des clients
    print(GENERAL_MESSAGES["db_creating_clients"])

    client1 = Client(
        full_name="Alice Rousseau",
        email="alice@techcorp.com",
        phone="01.23.45.67.89",
        company_name="TechCorp Solutions",
        commercial_contact_id=commercial1.id
    )
    session.add(client1)

    client2 = Client(
        full_name="Bob Moreau",
        email="bob@innovate.fr",
        phone="01.98.76.54.32",
        company_name="Innovate SARL",
        commercial_contact_id=commercial1.id
    )
    session.add(client2)

    client3 = Client(
        full_name="Catherine Leroy",
        email="c.leroy@startup.com",
        phone="01.11.22.33.44",
        company_name="StartUp Dynamics",
        commercial_contact_id=commercial2.id
    )
    session.add(client3)

    client4 = Client(
        full_name="David Lambert",
        email="d.lambert@bigcorp.fr",
        phone="01.55.66.77.88",
        company_name="BigCorp International",
        commercial_contact_id=commercial2.id
    )
    session.add(client4)

    session.commit()
    print(GENERAL_MESSAGES["db_clients_created"])

    # 3. Creer des contrats
    print(GENERAL_MESSAGES["db_creating_contracts"])

    # Contrat signe avec evenement
    contract1 = Contract(
        client_id=client1.id,
        commercial_contact_id=commercial1.id,
        total_amount=15000.00,
        amount_due=0.00,  # Paye
        status=ContractStatus.SIGNED,
        signed=True,
        signed_at=datetime.now() - timedelta(days=30)
    )
    session.add(contract1)

    # Contrat signe avec montant du
    contract2 = Contract(
        client_id=client2.id,
        commercial_contact_id=commercial1.id,
        total_amount=25000.00,
        amount_due=10000.00,
        status=ContractStatus.SIGNED,
        signed=True,
        signed_at=datetime.now() - timedelta(days=15)
    )
    session.add(contract2)

    # Contrat non signe
    contract3 = Contract(
        client_id=client3.id,
        commercial_contact_id=commercial2.id,
        total_amount=8000.00,
        amount_due=8000.00,
        status=ContractStatus.DRAFT,
        signed=False
    )
    session.add(contract3)

    # Contrat signe recemment
    contract4 = Contract(
        client_id=client4.id,
        commercial_contact_id=commercial2.id,
        total_amount=50000.00,
        amount_due=20000.00,
        status=ContractStatus.SIGNED,
        signed=True,
        signed_at=datetime.now() - timedelta(days=5)
    )
    session.add(contract4)

    session.commit()
    print(GENERAL_MESSAGES["db_contracts_created"])

    # 4. Creer des evenements
    print(GENERAL_MESSAGES["db_creating_events"])

    # Evenement passe avec support assigne
    event1 = Event(
        contract_id=contract1.id,
        name="Conference Tech 2024",
        location="Paris Convention Center",
        attendees=150,
        start_date=datetime.now() - timedelta(days=10),
        end_date=datetime.now() - timedelta(days=8),
        support_contact_id=support1.id,
        notes="Evenement reussi, client satisfait"
    )
    session.add(event1)

    # Evenement a venir avec support
    event2 = Event(
        contract_id=contract2.id,
        name="Lancement Produit Innovation",
        location="Lyon Eurexpo",
        attendees=300,
        start_date=datetime.now() + timedelta(days=20),
        end_date=datetime.now() + timedelta(days=22),
        support_contact_id=support1.id,
        notes="Preparation en cours"
    )
    session.add(event2)

    # Evenement sans support assigne
    event3 = Event(
        contract_id=contract4.id,
        name="Seminaire BigCorp",
        location="Nice Palais des Congres",
        attendees=80,
        start_date=datetime.now() + timedelta(days=45),
        end_date=datetime.now() + timedelta(days=47),
        support_contact_id=None,
        notes="En attente d'assignation support"
    )
    session.add(event3)

    # Evenement urgent (bientot)
    event4 = Event(
        contract_id=contract1.id,
        name="Workshop TechCorp",
        location="Marseille Centre d'Affaires",
        attendees=50,
        start_date=datetime.now() + timedelta(days=5),
        end_date=datetime.now() + timedelta(days=5),
        support_contact_id=support2.id,
        notes="Formation technique pour les employes"
    )
    session.add(event4)

    session.commit()
    print(GENERAL_MESSAGES["db_events_created"])

    print("\n=== DONNEES CREEES ===")
    print("Utilisateurs:")
    print("- admin@epicevents.com (mot de passe: Admin123!) - GESTION")
    print("- marie.martin@epicevents.com (mot de passe: Commercial123!) - COMMERCIAL")
    print("- pierre.durand@epicevents.com (mot de passe: Commercial123!) - COMMERCIAL")
    print("- sophie.bernard@epicevents.com (mot de passe: Support123!) - SUPPORT")
    print("- lucas.petit@epicevents.com (mot de passe: Support123!) - SUPPORT")
    print("\nClients: 4 crees")
    print("Contrats: 4 crees (2 signes avec montants dus, 1 signe paye, 1 non signe)")
    print("Evenements: 4 crees (1 passe, 2 a venir avec support, 1 sans support)")


def init_database():
    """Initialiser la base de donnees avec les tables et donnees d'exemple"""
    try:
        # Supprimer et recreer toutes les tables
        drop_all_tables()
        print(GENERAL_MESSAGES["db_creating_tables"])
        Base.metadata.create_all(bind=engine)
        print("Tables creees avec succes.")

        # Creer une session
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        try:
            # Creer les donnees d'exemple
            create_sample_data(session)

            print("\nBase de donnees initialisee avec succes!")
            return True

        except Exception as e:
            session.rollback()
            print(f"Erreur lors de la creation des donnees: {e}")
            return False
        finally:
            session.close()

    except Exception as e:
        print(f"Erreur lors de l'initialisation: {e}")
        return False


if __name__ == "__main__":
    init_database()
