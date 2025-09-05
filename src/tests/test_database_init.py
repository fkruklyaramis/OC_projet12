"""
Tests pour l'initialisation de la base de données
Fichier: src/tests/test_database_init.py
"""

from unittest.mock import patch, MagicMock
from src.database.init_db import init_database, create_sample_data, drop_all_tables
from src.database.connection import engine
from src.models.user import User, Department
from src.models.client import Client
from src.models.contract import Contract
from src.models.event import Event


class TestDatabaseInit:
    """Tests pour l'initialisation de la base de données"""

    def test_drop_all_tables(self, test_db):
        """Test de suppression de toutes les tables"""
        with patch('src.database.init_db.Base.metadata.drop_all') as mock_drop:
            drop_all_tables()
            mock_drop.assert_called_once_with(bind=engine)

    def test_create_all_tables(self, test_db):
        """Test de création de toutes les tables"""
        with patch('src.database.init_db.Base.metadata.create_all') as mock_create:
            init_database()
            mock_create.assert_called_once_with(bind=engine)

    def test_create_sample_data_users(self, test_db):
        """Test de création des utilisateurs d'exemple"""
        # Appliquer create_sample_data
        create_sample_data(test_db)
        test_db.commit()

        # Vérifier que des utilisateurs ont été créés
        users = test_db.query(User).all()
        assert len(users) >= 5  # Admin + 2 commerciaux + 2 support

        # Vérifier qu'on a au moins un utilisateur de chaque département
        departments = [user.department for user in users]
        assert Department.GESTION in departments
        assert Department.COMMERCIAL in departments
        assert Department.SUPPORT in departments

    def test_create_sample_data_clients(self, test_db):
        """Test de création des clients d'exemple"""
        create_sample_data(test_db)
        test_db.commit()

        # Vérifier que des clients ont été créés
        clients = test_db.query(Client).all()
        assert len(clients) >= 3

        # Vérifier qu'ils ont un contact commercial assigné
        for client in clients:
            assert client.commercial_contact_id is not None

    def test_create_sample_data_contracts(self, test_db):
        """Test de création des contrats d'exemple"""
        create_sample_data(test_db)
        test_db.commit()

        # Vérifier que des contrats ont été créés
        contracts = test_db.query(Contract).all()
        assert len(contracts) >= 3

        # Vérifier qu'ils sont liés à des clients
        for contract in contracts:
            assert contract.client_id is not None
            assert contract.total_amount > 0

    def test_create_sample_data_events(self, test_db):
        """Test de création des événements d'exemple"""
        create_sample_data(test_db)
        test_db.commit()

        # Vérifier que des événements ont été créés
        events = test_db.query(Event).all()
        assert len(events) >= 2

        # Vérifier qu'ils sont liés à des contrats
        for event in events:
            assert event.contract_id is not None

    def test_admin_user_creation(self, test_db):
        """Test de création spécifique de l'utilisateur admin"""
        create_sample_data(test_db)
        test_db.commit()

        # Chercher l'admin
        admin = test_db.query(User).filter_by(
            email="admin@epicevents.com"
        ).first()

        assert admin is not None
        assert admin.department == Department.GESTION
        assert admin.employee_number == "EE000001"
        assert admin.full_name == "Jean Dupont"

    def test_commercial_users_creation(self, test_db):
        """Test de création des utilisateurs commerciaux"""
        create_sample_data(test_db)
        test_db.commit()

        # Chercher les commerciaux
        commercials = test_db.query(User).filter_by(
            department=Department.COMMERCIAL
        ).all()

        assert len(commercials) >= 2

        # Vérifier les emails attendus
        emails = [user.email for user in commercials]
        assert "marie.martin@epicevents.com" in emails
        assert "pierre.durand@epicevents.com" in emails

    def test_support_users_creation(self, test_db):
        """Test de création des utilisateurs support"""
        create_sample_data(test_db)
        test_db.commit()

        # Chercher les utilisateurs support
        supports = test_db.query(User).filter_by(
            department=Department.SUPPORT
        ).all()

        assert len(supports) >= 2

        # Vérifier qu'ils ont des numéros d'employé différents
        employee_numbers = [user.employee_number for user in supports]
        assert len(set(employee_numbers)) == len(employee_numbers)

    def test_data_integrity(self, test_db):
        """Test de l'intégrité des données créées"""
        create_sample_data(test_db)
        test_db.commit()

        # Vérifier les relations
        clients = test_db.query(Client).all()
        for client in clients:
            # Chaque client doit avoir un contact commercial valide
            commercial = test_db.query(User).filter_by(
                id=client.commercial_contact_id
            ).first()
            assert commercial is not None
            assert commercial.department == Department.COMMERCIAL

        # Vérifier les contrats
        contracts = test_db.query(Contract).all()
        for contract in contracts:
            # Chaque contrat doit être lié à un client existant
            client = test_db.query(Client).filter_by(
                id=contract.client_id
            ).first()
            assert client is not None

        # Vérifier les événements
        events = test_db.query(Event).all()
        for event in events:
            # Chaque événement doit être lié à un contrat existant
            contract = test_db.query(Contract).filter_by(
                id=event.contract_id
            ).first()
            assert contract is not None

    @patch('src.database.init_db.sessionmaker')
    @patch('src.database.init_db.Base.metadata.create_all')
    def test_init_database_full_flow(self, mock_create_all, mock_sessionmaker):
        """Test du flux complet d'initialisation"""
        mock_session = MagicMock()
        mock_sessionmaker.return_value.return_value = mock_session

        init_database()

        # Vérifier que les tables sont créées
        mock_create_all.assert_called_once_with(bind=engine)

        # Vérifier qu'une session est créée et fermée
        mock_sessionmaker.assert_called_once_with(bind=engine)
        mock_session.close.assert_called_once()

    def test_unique_constraints(self, test_db):
        """Test des contraintes d'unicité"""
        create_sample_data(test_db)
        test_db.commit()

        # Vérifier l'unicité des emails
        users = test_db.query(User).all()
        emails = [user.email for user in users]
        assert len(emails) == len(set(emails))

        # Vérifier l'unicité des numéros d'employé
        employee_numbers = [user.employee_number for user in users]
        assert len(employee_numbers) == len(set(employee_numbers))

    def test_password_hashing(self, test_db):
        """Test que les mots de passe sont bien hachés"""
        create_sample_data(test_db)
        test_db.commit()

        admin = test_db.query(User).filter_by(
            email="admin@epicevents.com"
        ).first()

        # Le mot de passe ne doit pas être en clair
        assert admin.hashed_password != "Admin123!"
        # Le hash doit être non vide et suffisamment long
        assert len(admin.hashed_password) > 20
        assert admin.hashed_password.startswith('$argon2id$')  # argon2 prefix
