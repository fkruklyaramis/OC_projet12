from sqlalchemy import inspect
from src.database.connection import create_tables, engine


def init_database():
    """Initialiser la base de données avec toutes les tables"""
    try:
        print("Initialisation de la base de données...")

        # Créer toutes les tables
        create_tables()

        print("Tables créées avec succès:")
        print("- users (utilisateurs)")
        print("- clients")
        print("- contracts (contrats)")
        print("- events (événements)")

        # Vérifier que les tables existent
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"\nTables présentes dans la DB: {tables}")

        print("\nBase de données Epic Events CRM initialisée avec succès!")
        return True

    except Exception as e:
        print(f"Erreur lors de l'initialisation: {e}")
        return False


if __name__ == "__main__":
    init_database()
