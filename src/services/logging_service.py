"""
Service de journalisation avec Sentry pour Epic Events CRM
Fichier: src/services/logging_service.py
"""

import sentry_sdk
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from src.models.user import User


class Singleton(object):
    _instance = None

    def __new__(class_, *args, **kwargs):
        if not isinstance(class_._instance, class_):
            class_._instance = object.__new__(class_, *args, **kwargs)
        return class_._instance


class SentryLogger():
    """Service de journalisation avec Sentry pour Epic Events CRM"""

    def __init__(self):
        self.is_initialized = False
        self._setup_sentry()

    def __del__(self):
        if self.is_initialized:
            sentry_sdk.flush(timeout=2.0)

    def _setup_sentry(self):
        """Initialiser Sentry avec la configuration"""
        sentry_dsn = os.getenv('SENTRY_DSN')
        environment = os.getenv('SENTRY_ENVIRONMENT', 'development')

        if not sentry_dsn or sentry_dsn == 'your_sentry_dsn_here':
            logging.warning("Sentry DSN non configuré - journalisation désactivée")
            return

        try:
            sentry_sdk.init(
                dsn=sentry_dsn,
                environment=environment,
                traces_sample_rate=0.0,  # Désactiver complètement les traces
                profiles_sample_rate=0.0,  # Désactiver complètement les profiles
                shutdown_timeout=0,  # Pas d'attente à la fermeture
                default_integrations=False,  # Désactiver toutes les intégrations par défaut
                integrations=[],  # Pas d'intégrations du tout
            )
            self.is_initialized = True
            logging.info(f"Sentry initialisé avec succès - Environment: {environment}")

        except Exception as e:
            logging.error(f"Erreur lors de l'initialisation de Sentry: {e}")

    def set_user_context(self, user: User):
        """Définir le contexte utilisateur pour Sentry"""
        if not self.is_initialized:
            return

        sentry_sdk.set_user({
            "id": user.id,
            "email": user.email,
            "username": user.full_name,
            "department": user.department.value,
            "employee_number": user.employee_number
        })

    def clear_user_context(self):
        """Effacer le contexte utilisateur"""
        if not self.is_initialized:
            return

        sentry_sdk.set_user(None)

    def log_user_creation(self, created_user: User, creator: User):
        """Journaliser la création d'un collaborateur"""
        if not self.is_initialized:
            print("🔧 DEBUG: Sentry non initialisé - journalisation désactivée")
            return

        print(f"🔧 DEBUG: Envoi log création utilisateur {created_user.full_name} par {creator.full_name}")

        try:
            with sentry_sdk.configure_scope() as scope:
                scope.set_tag("action", "user_creation")
                scope.set_tag("department", created_user.department.value)
                scope.set_context("created_user", {
                    "id": created_user.id,
                    "email": created_user.email,
                    "full_name": created_user.full_name,
                    "department": created_user.department.value,
                    "employee_number": created_user.employee_number
                })
                scope.set_context("creator", {
                    "id": creator.id,
                    "email": creator.email,
                    "full_name": creator.full_name,
                    "department": creator.department.value
                })

            sentry_sdk.capture_message(
                f"Création d'un collaborateur: {created_user.full_name} ({created_user.email}) "
                f"par {creator.full_name}",
                level="info"  # Changed from "info" to "warning" pour plus de visibilité
            )

            print("✅ DEBUG: Log création utilisateur envoyé avec succès")

        except Exception as e:
            print(f"❌ DEBUG: Erreur lors de l'envoi du log: {e}")
            import traceback
            traceback.print_exc()

    def log_user_modification(self, modified_user: User, modifier: User, changes: Dict[str, Any]):
        """Journaliser la modification d'un collaborateur"""
        if not self.is_initialized:
            return

        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("action", "user_modification")
            scope.set_tag("department", modified_user.department.value)
            scope.set_context("modified_user", {
                "id": modified_user.id,
                "email": modified_user.email,
                "full_name": modified_user.full_name,
                "department": modified_user.department.value
            })
            scope.set_context("modifier", {
                "id": modifier.id,
                "email": modifier.email,
                "full_name": modifier.full_name,
                "department": modifier.department.value
            })
            scope.set_context("changes", changes)

        sentry_sdk.capture_message(
            f"Modification d'un collaborateur: {modified_user.full_name} "
            f"par {modifier.full_name} - Champs modifiés: {', '.join(changes.keys())}",
            level="info"
        )

    def log_contract_signature(self, contract, signer: User):
        """Journaliser la signature d'un contrat"""
        if not self.is_initialized:
            return

        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("action", "contract_signature")
            scope.set_tag("contract_id", str(contract.id))
            scope.set_context("contract", {
                "id": contract.id,
                "client_name": contract.client.company_name,
                "total_amount": float(contract.total_amount),
                "remaining_amount": float(contract.amount_due)  # Correct field name
            })
            scope.set_context("signer", {
                "id": signer.id,
                "email": signer.email,
                "full_name": signer.full_name,
                "department": signer.department.value
            })

        sentry_sdk.capture_message(
            f"Signature de contrat: ID {contract.id} pour {contract.client.company_name} "
            f"(Montant: {contract.total_amount}€) par {signer.full_name}",
            level="warning"  # Changed from "info" to "warning" pour plus de visibilité
        )

    def log_exception(self, exception: Exception, context: Optional[Dict[str, Any]] = None):
        """Journaliser une exception inattendue"""
        if not self.is_initialized:
            logging.error(f"Exception non gérée: {exception}")
            return

        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("action", "unexpected_exception")
            if context:
                scope.set_context("additional_context", context)

        sentry_sdk.capture_exception(exception)

    def log_authentication_attempt(self, email: str, success: bool, ip_address: str = None):
        """Journaliser une tentative d'authentification"""
        if not self.is_initialized:
            return

        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("action", "authentication_attempt")
            scope.set_tag("success", str(success))
            scope.set_context("auth_attempt", {
                "email": email,
                "timestamp": datetime.now().isoformat(),
                "ip_address": ip_address or "unknown",
                "success": success
            })

        level = "info" if success else "warning"
        status = "réussie" if success else "échouée"

        sentry_sdk.capture_message(
            f"Tentative de connexion {status} pour {email}",
            level=level
        )

    def shutdown(self):
        """Fermeture propre de Sentry"""
        if self.is_initialized:
            try:
                sentry_sdk.flush(timeout=2)  # Attendre max 2 secondes
            except Exception:
                pass  # Ignorer les erreurs de fermeture


sentry_logger = SentryLogger()
