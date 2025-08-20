from src.database.init_db import init_database


def main():
    """Point d'entrée principal de l'application Epic Events CRM"""
    print("=" * 50)
    print("    Bienvenue dans Epic Events CRM")
    print("=" * 50)

    # Initialiser la base de données
    if init_database():
        print("\nL'application est prête à être utilisée!")
    else:
        print("\nErreur lors de l'initialisation de la base de données.")
        return


if __name__ == "__main__":
    main()
