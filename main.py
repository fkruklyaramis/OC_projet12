from src.database.init_db import init_database
from src.config.messages import GENERAL_MESSAGES


def main():
    """Point d'entrée principal de l'application Epic Events CRM"""
    print("=" * 50)
    print(GENERAL_MESSAGES["app_welcome"])
    print("=" * 50)

    # Initialiser la base de données
    if init_database():
        print(GENERAL_MESSAGES["app_ready"])
    else:
        print(GENERAL_MESSAGES["app_init_error"])
        return


if __name__ == "__main__":
    main()
