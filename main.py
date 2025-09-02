from src.database.init_db import init_database
from src.config.messages import GENERAL_MESSAGES
from src.services.logging_service import sentry_logger
from src.utils.exception_handler import ExceptionHandler
from dotenv import load_dotenv
import atexit


def main():
    """Point d'entrée principal de l'application Epic Events CRM"""
    # Charger les variables d'environnement
    load_dotenv()

    # Configurer le gestionnaire global d'exceptions
    ExceptionHandler.setup_global_exception_handler()

    # Configurer la fermeture propre de Sentry
    atexit.register(lambda: sentry_logger.shutdown())

    try:
        print("=" * 50)
        print(GENERAL_MESSAGES["app_welcome"])
        print("=" * 50)

        # Initialiser la base de données
        if init_database():
            print(GENERAL_MESSAGES["app_ready"])
        else:
            print(GENERAL_MESSAGES["app_init_error"])
            return

    except Exception as e:
        sentry_logger.log_exception(e, {"context": "application_startup"})


if __name__ == "__main__":
    main()
