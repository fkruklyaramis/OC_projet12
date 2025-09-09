"""
Service de journalisation avec Sentry pour Epic Events CRM
Fichier: src/services/logging_service.py
"""

import sentry_sdk
import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from src.models.user import User


class SentryLogger:
    """Service de journalisation simple avec Sentry"""

    def __init__(self):
        self.is_initialized = False
        self._setup_sentry()

    def __del__(self):
        """Flush des données Sentry avant destruction"""
        if hasattr(self, 'is_initialized') and self.is_initialized:
            try:
                sentry_sdk.flush(timeout=2)
            except Exception:
                pass  # Ignorer les erreurs lors du flush

    def _setup_sentry(self):
        """Initialiser Sentry avec configuration simple"""
        sentry_dsn = os.getenv('SENTRY_DSN')
        environment = os.getenv('SENTRY_ENVIRONMENT', 'development')

        # Ne pas initialiser en mode test
        if os.getenv('PYTEST_CURRENT_TEST'):
            logging.info("Mode test détecté - Sentry désactivé")
            return

        if not sentry_dsn or sentry_dsn == 'your_sentry_dsn_here':
            logging.warning("Sentry DSN non configuré - journalisation désactivée")
            return

        try:
            # Configuration Sentry simple et robuste
            sentry_sdk.init(
                dsn=sentry_dsn,
                environment=environment,
                traces_sample_rate=0.0,  # Pas de tracing pour simplifier
                profiles_sample_rate=0.0,  # Pas de profiling
                max_breadcrumbs=50,
                debug=False,
                attach_stacktrace=True,
                send_default_pii=False,  # Pas d'infos personnelles par défaut
            )
            self.is_initialized = True
            logging.info(f"Sentry initialisé - Environment: {environment}")

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
            return

        with sentry_sdk.push_scope() as scope:
            scope.set_tag("action", "user_creation")
            scope.set_tag("department", created_user.department.value)
            scope.set_extra("created_user", {
                "id": created_user.id,
                "email": created_user.email,
                "full_name": created_user.full_name,
                "department": created_user.department.value,
                "employee_number": created_user.employee_number
            })
            scope.set_extra("creator", {
                "id": creator.id,
                "email": creator.email,
                "full_name": creator.full_name,
                "department": creator.department.value
            })

            sentry_sdk.capture_message(
                f"Création collaborateur: {created_user.full_name} par {creator.full_name}",
                level="info"
            )

    def log_user_modification(self, modified_user: User, modifier: User, changes: Dict[str, Any]):
        """Journaliser la modification d'un collaborateur"""
        if not self.is_initialized:
            return

        with sentry_sdk.push_scope() as scope:
            scope.set_tag("action", "user_modification")
            scope.set_extra("modified_user", modified_user.full_name)
            scope.set_extra("modifier", modifier.full_name)
            scope.set_extra("changes", changes)

            sentry_sdk.capture_message(
                f"Modification collaborateur: {modified_user.full_name} par {modifier.full_name}",
                level="info"
            )

    def log_contract_signature(self, contract, signer: User):
        """Journaliser la signature d'un contrat"""
        if not self.is_initialized:
            return

        with sentry_sdk.push_scope() as scope:
            scope.set_tag("action", "contract_signature")
            scope.set_tag("contract_id", str(contract.id))
            scope.set_extra("contract", {
                "id": contract.id,
                "client_name": contract.client.company_name,
                "total_amount": float(contract.total_amount),
            })
            scope.set_extra("signer", signer.full_name)

            sentry_sdk.capture_message(
                f"Signature contrat ID {contract.id} par {signer.full_name}",
                level="warning"
            )

    def log_exception(self, exception: Exception, context: Optional[Dict[str, Any]] = None):
        """Journaliser une exception"""
        if not self.is_initialized:
            logging.error(f"Exception: {exception}")
            return

        with sentry_sdk.push_scope() as scope:
            scope.set_tag("action", "exception")
            if context:
                scope.set_extra("context", context)

            sentry_sdk.capture_exception(exception)

    def log_authentication_attempt(self, email: str, success: bool, ip_address: str = None):
        """Journaliser une tentative d'authentification"""
        if not self.is_initialized:
            return

        with sentry_sdk.push_scope() as scope:
            scope.set_tag("action", "authentication")
            scope.set_tag("success", str(success))
            scope.set_extra("auth_attempt", {
                "email": email,
                "success": success,
                "ip_address": ip_address or "unknown",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            level = "info" if success else "warning"
            status = "réussie" if success else "échouée"

            sentry_sdk.capture_message(
                f"Connexion {status}: {email}",
                level=level
            )

    def force_flush(self):
        """Forcer l'envoi immédiat des données vers Sentry"""
        if self.is_initialized:
            try:
                sentry_sdk.flush(timeout=5)
            except Exception:
                pass
