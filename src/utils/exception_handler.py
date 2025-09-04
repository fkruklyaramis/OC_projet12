"""
Gestionnaire global des exceptions pour Epic Events CRM
Fichier: src/utils/exception_handler.py
"""

import sys
import traceback
from typing import Any, Callable, TypeVar, Optional
from functools import wraps
from src.services.logging_service import SentryLogger


F = TypeVar('F', bound=Callable[..., Any])


def handle_exceptions(reraise: bool = True) -> Callable[[F], F]:
    """
    Décorateur pour gérer automatiquement les exceptions avec Sentry

    Args:
        reraise: Si True, relance l'exception après l'avoir loggée
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Journaliser l'exception avec contexte
                context = {
                    'function_name': func.__name__,
                    'module': func.__module__,
                    'args_count': len(args),
                    'kwargs_keys': list(kwargs.keys()) if kwargs else []
                }

                SentryLogger().log_exception(e, context)

                if reraise:
                    raise
                return None

        return wrapper
    return decorator


class ExceptionHandler:
    """Gestionnaire global des exceptions pour l'application"""

    @staticmethod
    def setup_global_exception_handler():
        """Configurer le gestionnaire d'exceptions global"""
        def exception_handler(exc_type, exc_value, exc_traceback):
            """Gestionnaire global d'exceptions non capturées"""
            if issubclass(exc_type, KeyboardInterrupt):
                # Ne pas logger les interruptions clavier
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return

            # Préparer le contexte
            context = {
                'exception_type': exc_type.__name__,
                'traceback': ''.join(traceback.format_exception(
                    exc_type, exc_value, exc_traceback
                )),
                'global_exception': True
            }

            # Journaliser avec Sentry
            SentryLogger().log_exception(exc_value, context)

            # Afficher l'erreur à l'utilisateur
            print(f"\n❌ Une erreur inattendue s'est produite: {exc_value}")
            print("L'erreur a été automatiquement reportée pour analyse.")

            # Appeler le gestionnaire par défaut aussi
            sys.__excepthook__(exc_type, exc_value, exc_traceback)

        # Installer le gestionnaire
        sys.excepthook = exception_handler

    @staticmethod
    def safe_execute(func: Callable, *args, **kwargs) -> Optional[Any]:
        """
        Exécuter une fonction de manière sécurisée avec gestion d'exceptions

        Args:
            func: Fonction à exécuter
            *args: Arguments positionnels
            **kwargs: Arguments nommés

        Returns:
            Résultat de la fonction ou None si erreur
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            context = {
                'function_name': getattr(func, '__name__', 'unknown'),
                'safe_execution': True,
                'args_provided': len(args) > 0,
                'kwargs_provided': len(kwargs) > 0
            }

            SentryLogger().log_exception(e, context)
            return None


# Instance globale
exception_handler = ExceptionHandler()
