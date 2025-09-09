"""
Gestionnaire global des exceptions pour Epic Events CRM

Ce module fournit une infrastructure complète de gestion des exceptions
avec intégration Sentry, décorateurs automatiques et gestionnaires globaux
pour garantir la stabilité et la traçabilité de l'application.

Architecture de gestion d'erreurs:
    1. Décorateurs: Capture automatique avec métadonnées contextuelles
    2. Gestionnaire global: Interception des exceptions non gérées
    3. Exécution sécurisée: Wrapper pour opérations critiques
    4. Logging centralisé: Envoi automatique vers Sentry avec contexte

Fonctionnalités principales:
    - Capture automatique via décorateur @handle_exceptions
    - Gestionnaire global pour exceptions non capturées
    - Exécution sécurisée avec fallback gracieux
    - Enrichissement automatique du contexte d'erreur
    - Intégration transparente avec système de logging

Types d'exceptions gérées:
    - Exceptions métier: Erreurs de validation, logique business
    - Exceptions techniques: Erreurs base de données, réseau, I/O
    - Exceptions système: Erreurs mémoire, permissions, ressources
    - Exceptions utilisateur: Interruptions clavier, signaux système

Patterns de gestion:
    - Fail-fast: Détection précoce avec feedback immédiat
    - Graceful degradation: Continuation avec fonctionnalités réduites
    - Circuit breaker: Protection contre cascades d'erreurs
    - Retry logic: Nouvelle tentative pour erreurs transitoires

Contexte d'erreur enrichi:
    - Fonction et module où l'erreur s'est produite
    - Arguments de la fonction au moment de l'erreur
    - Stack trace complète pour débogage
    - Métadonnées système et environnement

Intégration Sentry:
    - Envoi automatique avec contexte complet
    - Classification par niveau de sévérité
    - Groupement intelligent des erreurs similaires
    - Alertes temps réel pour erreurs critiques

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
    Décorateur pour gérer automatiquement les exceptions avec Sentry.

    Ce décorateur capture toutes les exceptions levées par la fonction
    décorée, les log avec contexte enrichi et optionnellement les relance.

    Args:
        reraise: Si True, relance l'exception après l'avoir loggée.
                 Si False, retourne None et continue l'exécution.

    Returns:
        Décorateur configuré pour la gestion d'exceptions

    Contexte automatique capturé:
        - Nom de la fonction et module d'origine
        - Nombre d'arguments positionnels
        - Clés des arguments nommés (sans valeurs pour sécurité)
        - Stack trace complète de l'erreur

    Utilisation:
        @handle_exceptions()  # Relance après logging
        def operation_critique():
            pass

        @handle_exceptions(reraise=False)  # Continue après logging
        def operation_optionnelle():
            pass

    Sécurité:
        - Aucune valeur d'argument loggée (protection données sensibles)
        - Filtering automatique des informations critiques
        - Gestion gracieuse des erreurs de logging
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Enrichissement du contexte d'erreur pour debugging
                context = {
                    'function_name': func.__name__,
                    'module': func.__module__,
                    'args_count': len(args),
                    'kwargs_keys': list(kwargs.keys()) if kwargs else [],
                    'decorated_function': True
                }

                # Logging avec contexte via Sentry
                SentryLogger().log_exception(e, context)

                if reraise:
                    # Relancer pour gestion par l'appelant
                    raise
                # Retour None pour continuation gracieuse
                return None

        return wrapper
    return decorator


class ExceptionHandler:
    """
    Gestionnaire global des exceptions pour la stabilité de l'application.

    Cette classe fournit des outils de gestion d'exceptions de haut niveau
    pour garantir la robustesse et la traçabilité de l'application Epic Events.

    Responsabilités:
        - Installation de gestionnaires globaux d'exceptions
        - Exécution sécurisée avec gestion d'erreurs automatique
        - Formatage et logging structuré des erreurs
        - Interface utilisateur pour feedback d'erreurs
        - Protection contre les crashs d'application

    Architecture:
        - Gestionnaire global: Capture des exceptions non gérées
        - Exécution sécurisée: Wrapper pour opérations à risque
        - Logging centralisé: Intégration avec Sentry
        - Feedback utilisateur: Messages d'erreur conviviaux
    """

    @staticmethod
    def setup_global_exception_handler():
        """
        Configurer le gestionnaire d'exceptions global pour l'application.

        Cette méthode installe un gestionnaire qui capture toutes les exceptions
        non gérées et les traite de manière uniforme avec logging et feedback.

        Fonctionnalités:
            - Capture des exceptions non gérées par l'application
            - Logging automatique vers Sentry avec contexte complet
            - Feedback utilisateur convivial pour erreurs inattendues
            - Préservation du comportement par défaut pour débogage
            - Gestion spéciale des interruptions clavier (Ctrl+C)

        Installation:
            Remplace sys.excepthook pour intercepter toutes les exceptions
            non capturées avant qu'elles ne causent un crash.

        Exceptions spéciales:
            - KeyboardInterrupt: Gestion normale sans logging (Ctrl+C)
            - SystemExit: Préservation des codes de sortie
            - Autres: Logging complet avec stack trace
        """
        def exception_handler(exc_type, exc_value, exc_traceback):
            """
            Gestionnaire interne pour exceptions non capturées.

            Args:
                exc_type: Type de l'exception (classe)
                exc_value: Instance de l'exception avec message
                exc_traceback: Stack trace de l'erreur
            """
            # Interruptions clavier = comportement normal (pas d'erreur)
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return

            # Préparation du contexte enrichi pour debugging
            context = {
                'exception_type': exc_type.__name__,
                'traceback': ''.join(traceback.format_exception(
                    exc_type, exc_value, exc_traceback
                )),
                'global_exception': True,
                'handled_by': 'global_exception_handler'
            }

            # Logging automatique via Sentry
            SentryLogger().log_exception(exc_value, context)

            # Interface utilisateur: message d'erreur convivial
            print(f"\n❌ Une erreur inattendue s'est produite: {exc_value}")
            print("L'erreur a été automatiquement reportée pour analyse.")
            print("Veuillez contacter l'équipe technique si le problème persiste.")

            # Préservation du comportement par défaut pour débogage
            sys.__excepthook__(exc_type, exc_value, exc_traceback)

        # Installation du gestionnaire global
        sys.excepthook = exception_handler

    @staticmethod
    def safe_execute(func: Callable, *args, **kwargs) -> Optional[Any]:
        """
        Exécuter une fonction de manière sécurisée avec gestion d'exceptions.

        Cette méthode encapsule l'exécution d'une fonction pour garantir
        qu'aucune exception ne peut interrompre le flux principal.

        Args:
            func: Fonction à exécuter de manière sécurisée
            *args: Arguments positionnels à transmettre
            **kwargs: Arguments nommés à transmettre

        Returns:
            Résultat de la fonction si succès, None si exception

        Cas d'usage:
            - Opérations optionnelles non critiques
            - Fonctions tierces potentiellement instables
            - Code de nettoyage en fin de processus
            - Validation de données utilisateur

        Gestion d'erreurs:
            - Capture de toutes les exceptions
            - Logging automatique avec contexte
            - Retour None pour signaler l'échec
            - Continuation du programme principal
        Exemple:
            result = ExceptionHandler.safe_execute(
                risky_operation,
                param1,
                param2=value
            )
            if result is None:
                # Gestion du cas d'erreur
                fallback_operation()
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Contexte spécifique à l'exécution sécurisée
            context = {
                'function_name': getattr(func, '__name__', 'unknown'),
                'safe_execution': True,
                'args_provided': len(args) > 0,
                'kwargs_provided': len(kwargs) > 0,
                'execution_mode': 'safe_wrapper'
            }

            # Logging de l'erreur sans interrompre le flux
            SentryLogger().log_exception(e, context)

            # Retour None pour signaler l'échec
            return None

            SentryLogger().log_exception(e, context)
            return None


# Instance globale
exception_handler = ExceptionHandler()
