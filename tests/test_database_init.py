import os
from sqlalchemy import inspect
from src.database.init_db import init_database
from src.database.connection import engine


def test_database_initialization():
    """Tester l'initialisation de la base de données"""
    db_file = "epic_events.db"
    if os.path.exists(db_file):
        os.remove(db_file)

    result = init_database()
    assert result is True
    assert os.path.exists(db_file)


def test_tables_creation():
    """Tester que toutes les tables sont créées"""
    init_database()

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    expected_tables = ['users', 'clients', 'contracts', 'events']
    for table in expected_tables:
        assert table in tables, f"La table {table} n'a pas été créée"


def test_table_structure():
    """Tester la structure des tables"""
    init_database()

    inspector = inspect(engine)

    user_columns = [col['name'] for col in inspector.get_columns('users')]
    expected_user_cols = ['id', 'employee_number', 'email', 'hashed_password',
                          'full_name', 'department']
    for col in expected_user_cols:
        assert col in user_columns, f"Colonne {col} manquante dans table users"

    client_columns = [col['name'] for col in inspector.get_columns('clients')]
    expected_client_cols = ['id', 'full_name', 'email', 'phone', 'company_name',
                            'commercial_contact_id']
    for col in expected_client_cols:
        assert col in client_columns, f"Colonne {col} manquante dans table clients"


def test_user_constraints():
    """Tester les contraintes sur la table users"""
    init_database()

    inspector = inspect(engine)
    indexes = inspector.get_indexes('users')

    # Vérifier que les index existent
    indexed_columns = []
    for index in indexes:
        indexed_columns.extend(index['column_names'])

    assert 'employee_number' in indexed_columns
    assert 'email' in indexed_columns
