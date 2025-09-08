"""
Tests pour l'initialisation de la base de données
Fichier: tests/test_database_init.py
"""
import unittest
from unittest.mock import patch, MagicMock
from src.database.init_db import init_database, drop_all_tables, create_sample_data


class TestDatabaseInit(unittest.TestCase):
    """Tests pour l'initialisation de la base de données"""

    @patch('src.database.init_db.Base')
    @patch('src.database.init_db.engine')
    def test_drop_all_tables(self, mock_engine, mock_base):
        """Test suppression de toutes les tables"""
        mock_metadata = MagicMock()
        mock_base.metadata = mock_metadata

        drop_all_tables()

        mock_metadata.drop_all.assert_called_once_with(bind=mock_engine)

    @patch('src.database.init_db.Base')
    @patch('src.database.init_db.engine')
    def test_create_tables(self, mock_engine, mock_base):
        """Test création des tables"""
        mock_metadata = MagicMock()
        mock_base.metadata = mock_metadata

        # Simuler la création des tables
        mock_metadata.create_all(bind=mock_engine)

        mock_metadata.create_all.assert_called_once_with(bind=mock_engine)

    @patch('src.database.init_db.hash_password')
    def test_create_sample_data(self, mock_hash_password):
        """Test création des données d'exemple"""
        mock_hash_password.return_value = "hashed_password"

        # Mock session
        mock_session = MagicMock()

        # Simuler des IDs pour les utilisateurs
        mock_user1 = MagicMock()
        mock_user1.id = 1
        mock_user2 = MagicMock()
        mock_user2.id = 2

        # Mock les objets ajoutés à la session
        added_objects = []

        def mock_add(obj):
            if hasattr(obj, 'id'):
                if isinstance(obj, type(mock_user1)):
                    obj.id = len(added_objects) + 1
            added_objects.append(obj)

        mock_session.add.side_effect = mock_add

        create_sample_data(mock_session)

        # Vérifier que la session a été utilisée
        self.assertTrue(mock_session.add.called)
        self.assertTrue(mock_session.commit.called)

    @patch('src.database.init_db.sessionmaker')
    @patch('src.database.init_db.Base')
    @patch('src.database.init_db.engine')
    @patch('src.database.init_db.create_sample_data')
    def test_init_database_success(self, mock_create_data, mock_engine, mock_base, mock_sessionmaker):
        """Test initialisation réussie de la base de données"""
        # Mock metadata
        mock_metadata = MagicMock()
        mock_base.metadata = mock_metadata

        # Mock session
        mock_session = MagicMock()
        mock_sessionmaker.return_value.return_value = mock_session

        # Mock create_sample_data pour qu'elle ne lève pas d'exception
        mock_create_data.return_value = None

        result = init_database()

        # Vérifications
        self.assertTrue(result)
        mock_metadata.drop_all.assert_called_once_with(bind=mock_engine)
        mock_metadata.create_all.assert_called_once_with(bind=mock_engine)
        mock_create_data.assert_called_once_with(mock_session)
        mock_session.close.assert_called_once()

    @patch('src.database.init_db.sessionmaker')
    @patch('src.database.init_db.Base')
    @patch('src.database.init_db.engine')
    @patch('src.database.init_db.create_sample_data')
    def test_init_database_create_data_error(self, mock_create_data, mock_engine, mock_base, mock_sessionmaker):
        """Test gestion d'erreur lors de la création des données"""
        # Mock metadata
        mock_metadata = MagicMock()
        mock_base.metadata = mock_metadata

        # Mock session
        mock_session = MagicMock()
        mock_sessionmaker.return_value.return_value = mock_session

        # Mock create_sample_data pour qu'elle lève une exception
        mock_create_data.side_effect = Exception("Erreur de création")

        result = init_database()

        # Vérifications
        self.assertFalse(result)
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch('src.database.init_db.Base')
    @patch('src.database.init_db.engine')
    def test_init_database_table_creation_error(self, mock_engine, mock_base):
        """Test gestion d'erreur lors de la création des tables"""
        # Mock metadata pour lever une exception
        mock_metadata = MagicMock()
        mock_metadata.create_all.side_effect = Exception("Erreur de création de table")
        mock_base.metadata = mock_metadata

        result = init_database()

        # Vérifications
        self.assertFalse(result)

    @patch('src.database.init_db.hash_password')
    def test_create_sample_users(self, mock_hash_password):
        """Test création des utilisateurs d'exemple"""
        mock_hash_password.return_value = "hashed_password"
        mock_session = MagicMock()

        # Compter les appels d'ajout d'utilisateurs
        user_count = 0

        def count_users(obj):
            nonlocal user_count
            if hasattr(obj, 'department'):  # Indicateur d'un objet User
                user_count += 1

        mock_session.add.side_effect = count_users

        create_sample_data(mock_session)

        # Vérifier qu'au moins 5 utilisateurs ont été créés
        self.assertGreaterEqual(user_count, 5)

    @patch('src.database.init_db.hash_password')
    def test_create_sample_clients(self, mock_hash_password):
        """Test création des clients d'exemple"""
        mock_hash_password.return_value = "hashed_password"
        mock_session = MagicMock()

        # Compter les appels d'ajout de clients
        client_count = 0

        def count_clients(obj):
            nonlocal client_count
            if hasattr(obj, 'company_name'):  # Indicateur d'un objet Client
                client_count += 1

        mock_session.add.side_effect = count_clients

        create_sample_data(mock_session)

        # Vérifier qu'au moins 4 clients ont été créés
        self.assertGreaterEqual(client_count, 4)

    @patch('src.database.init_db.hash_password')
    def test_create_sample_contracts(self, mock_hash_password):
        """Test création des contrats d'exemple"""
        mock_hash_password.return_value = "hashed_password"
        mock_session = MagicMock()

        # Compter les appels d'ajout de contrats
        contract_count = 0

        def count_contracts(obj):
            nonlocal contract_count
            if hasattr(obj, 'total_amount'):  # Indicateur d'un objet Contract
                contract_count += 1

        mock_session.add.side_effect = count_contracts

        create_sample_data(mock_session)

        # Vérifier qu'au moins 4 contrats ont été créés
        self.assertGreaterEqual(contract_count, 4)

    @patch('src.database.init_db.hash_password')
    def test_create_sample_events(self, mock_hash_password):
        """Test création des événements d'exemple"""
        mock_hash_password.return_value = "hashed_password"
        mock_session = MagicMock()

        # Compter les appels d'ajout d'événements
        event_count = 0

        def count_events(obj):
            nonlocal event_count
            if hasattr(obj, 'attendees'):  # Indicateur d'un objet Event
                event_count += 1

        mock_session.add.side_effect = count_events

        create_sample_data(mock_session)

        # Vérifier qu'au moins 4 événements ont été créés
        self.assertGreaterEqual(event_count, 4)


if __name__ == '__main__':
    unittest.main()
