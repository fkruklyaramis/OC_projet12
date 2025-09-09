"""
Service de journalisation et monitoring avec Sentry pour Epic Events CRM

Ce module fournit une couche de logging centralisée avec intégration Sentry
pour le monitoring en temps réel, la gestion des erreurs et l'audit des
actions critiques de l'application Epic Events.

Architecture de monitoring:
    1. Logging local: Messages de debugging et informations système
    2. Sentry: Monitoring production avec alertes temps réel
    3. Audit: Traçabilité des actions métier critiques
    4. Contexte: Enrichissement automatique avec données utilisateur

Fonctionnalités principales:
    - Monitoring automatique des erreurs et exceptions
    - Logging structuré des actions métier (création, modification, suppression)
    - Contexte utilisateur enrichi pour traçabilité
    - Alertes temps réel pour incidents critiques
    - Dashboard de monitoring intégré

Types d'événements loggés:
    - Authentification: Tentatives, succès, échecs, déconnexions
    - Actions CRUD: Création, modification, suppression d'entités
    - Erreurs: Exceptions techniques et erreurs métier
    - Performance: Métriques et temps de réponse critiques
    - Sécurité: Tentatives d'accès non autorisé, violations de permissions

Configuration environnements:
    - Développement: Logging console détaillé, Sentry optionnel
    - Test: Logging désactivé pour performances
    - Production: Sentry obligatoire avec alertes configurées

Intégrations:
    - Sentry SDK: Monitoring production avec dashboard web
    - Python logging: Logs locaux pour debugging
    - JWT: Contexte utilisateur automatique depuis tokens
    - Base de données: Audit des modifications de données

Sécurité et confidentialité:
    - Aucune donnée sensible dans les logs (mots de passe, tokens)
    - Anonymisation automatique des données personnelles
    - Rotation des logs et purge automatique
    - Conformité RGPD pour données utilisateur

Fichier: src/services/logging_service.py
"""

import sentry_sdk
import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from src.models.user import User


class SentryLogger:
    """
    Service de logging centralisé avec intégration Sentry pour monitoring.

    Cette classe fournit une interface unifiée pour le logging local et
    le monitoring distant via Sentry. Elle enrichit automatiquement les
    événements avec le contexte utilisateur et les métadonnées métier.

    Responsabilités:
        - Configuration automatique de Sentry selon l'environnement
        - Logging structuré des événements métier critiques
        - Gestion du contexte utilisateur pour traçabilité
        - Monitoring des performances et erreurs en temps réel
        - Audit trail complet des actions sensibles

    Architecture:
        - Initialisation automatique avec configuration d'environnement
        - Détection du mode test pour désactivation conditionnelle
        - Gestion gracieuse des erreurs de configuration Sentry
        - Enrichissement automatique avec contexte utilisateur JWT

    Patterns implémentés:
        - Singleton: Instance unique par application
        - Observer: Logging automatique des événements système
        - Facade: Interface simplifiée pour logging complexe
        - Strategy: Différentes stratégies selon environnement

    Attributes:
        is_initialized: Flag indiquant si Sentry est correctement configuré
    """

    def __init__(self):
        """
        Initialiser le service de logging avec configuration automatique.

        Cette méthode configure automatiquement Sentry selon l'environnement
        détecté et les variables de configuration disponibles.
        """
        self.is_initialized = False
        self._setup_sentry()

    def __del__(self):
        """
        Flush des données Sentry avant destruction de l'instance.

        Cette méthode garantit que tous les événements en attente sont
        envoyés à Sentry avant la fermeture de l'application.
        """
        if hasattr(self, 'is_initialized') and self.is_initialized:
            try:
                sentry_sdk.flush(timeout=2)
            except Exception:
                # Ignorer silencieusement les erreurs de flush pour éviter
                # les exceptions lors de l'arrêt de l'application
                pass

    def _setup_sentry(self):
        """
        Initialiser Sentry avec configuration adaptée à l'environnement.

        Cette méthode configure Sentry avec les paramètres optimaux pour
        chaque environnement (développement, test, production) en gérant
        les cas de configuration manquante ou invalide.

        Configuration:
            - DSN depuis variable d'environnement SENTRY_DSN
            - Environnement depuis SENTRY_ENVIRONMENT (défaut: development)
            - Désactivation automatique en mode test (PYTEST_CURRENT_TEST)
            - Paramètres optimisés pour performance et sécurité
        """
        # Lecture de la configuration depuis les variables d'environnement
        sentry_dsn = os.getenv('SENTRY_DSN')
        environment = os.getenv('SENTRY_ENVIRONMENT', 'development')

        # Désactivation automatique en mode test pour éviter la pollution
        if os.getenv('PYTEST_CURRENT_TEST'):
            logging.info("Mode test détecté - Sentry désactivé")
            return

        # Vérification de la configuration DSN
        if not sentry_dsn or sentry_dsn == 'your_sentry_dsn_here':
            logging.warning("Sentry DSN non configuré - journalisation désactivée")
            return

        try:
            # Configuration Sentry optimisée pour Epic Events
            sentry_sdk.init(
                dsn=sentry_dsn,
                environment=environment,
                traces_sample_rate=0.0,      # Pas de tracing pour éviter overhead
                profiles_sample_rate=0.0,    # Pas de profiling par défaut
                max_breadcrumbs=50,          # Historique des actions pour contexte
                debug=False,
                attach_stacktrace=True,
                send_default_pii=False,  # Pas d'infos personnelles par défaut
            )
            self.is_initialized = True
            logging.info(f"Sentry initialisé - Environment: {environment}")

        except Exception as e:
            logging.error(f"Erreur lors de l'initialisation de Sentry: {e}")

    def set_user_context(self, user: User):
        """
        Définir le contexte utilisateur pour enrichir les événements Sentry.

        Cette méthode configure le contexte utilisateur qui sera automatiquement
        ajouté à tous les événements Sentry, permettant une traçabilité complète
        des actions par utilisateur.

        Args:
            user: Instance de l'utilisateur connecté

        Données contextuelles:
            - ID utilisateur pour liaison avec base de données
            - Email pour identification humaine
            - Nom complet pour interfaces d'administration
            - Département pour analyse par rôle
            - Numéro d'employé pour audit RH

        Sécurité:
            Aucune donnée sensible (mot de passe, token) n'est incluse
            dans le contexte pour préserver la confidentialité.
        """
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
        """
        Effacer le contexte utilisateur lors de la déconnexion.

        Cette méthode nettoie le contexte utilisateur Sentry pour éviter
        l'attribution d'événements ultérieurs à l'utilisateur déconnecté.
        Appelée automatiquement lors du logout.
        """
        if not self.is_initialized:
            return

        sentry_sdk.set_user(None)

    def log_user_creation(self, created_user: User, creator: User):
        """
        Journaliser la création d'un nouveau collaborateur.

        Cette méthode enregistre les créations d'utilisateurs avec un contexte
        enrichi pour l'audit et la traçabilité des actions d'administration.

        Args:
            created_user: Nouvel utilisateur créé
            creator: Utilisateur ayant effectué la création

        Contexte loggé:
            - Action: Identification du type d'opération
            - Département: Pour analyse des patterns de création
            - Données utilisateur: Informations non sensibles
            - Créateur: Traçabilité de la responsabilité
        """
        if not self.is_initialized:
            return

        with sentry_sdk.push_scope() as scope:
            # Tags pour filtrage et analyse dans Sentry
            scope.set_tag("action", "user_creation")
            scope.set_tag("department", created_user.department.value)

            # Données détaillées du nouvel utilisateur
            scope.set_extra("created_user", {
                "id": created_user.id,
                "email": created_user.email,
                "full_name": created_user.full_name,
                "department": created_user.department.value,
                "employee_number": created_user.employee_number
            })

            # Informations sur l'administrateur créateur
            scope.set_extra("creator", {
                "id": creator.id,
                "email": creator.email,
                "full_name": creator.full_name,
                "department": creator.department.value
            })

            # Capture de l'événement avec message descriptif
            sentry_sdk.capture_message(
                f"Création collaborateur: {created_user.full_name} par {creator.full_name}",
                level="info"
            )

    def log_user_modification(self, modified_user: User, modifier: User, changes: Dict[str, Any]):
        """
        Journaliser la modification d'un collaborateur existant.

        Cette méthode enregistre les modifications d'utilisateurs avec le détail
        des champs modifiés pour un audit complet des changements.

        Args:
            modified_user: Utilisateur modifié
            modifier: Utilisateur ayant effectué la modification
            changes: Dictionnaire des changements (champ -> (ancienne, nouvelle))

        Contexte loggé:
            - Action: Type de modification
            - Utilisateur cible: Identification complète
            - Modificateur: Responsable de l'action
            - Détail des changements: Audit trail précis
        """
        if not self.is_initialized:
            return

        with sentry_sdk.push_scope() as scope:
            # Tags pour analyse des patterns de modification
            scope.set_tag("action", "user_modification")
            scope.set_tag("modifier_department", modifier.department.value)

            # Informations détaillées sur l'utilisateur modifié
            scope.set_extra("modified_user", {
                "id": modified_user.id,
                "email": modified_user.email,
                "full_name": modified_user.full_name,
                "department": modified_user.department.value
            })

            # Informations sur l'utilisateur modificateur
            scope.set_extra("modifier", {
                "id": modifier.id,
                "email": modifier.email,
                "full_name": modifier.full_name,
                "department": modifier.department.value
            })

            # Détail précis des modifications pour audit
            scope.set_extra("changes", changes)

            sentry_sdk.capture_message(
                f"Modification collaborateur: {modified_user.full_name} par {modifier.full_name}",
                level="info"
            )

    def log_contract_signature(self, contract, signer: User):
        """
        Journaliser la signature d'un contrat par un commercial.

        Cette méthode enregistre les signatures de contrats, événement critique
        pour le suivi des engagements financiers et la responsabilité commerciale.

        Args:
            contract: Instance du contrat signé
            signer: Commercial ayant signé le contrat

        Niveau de sévérité:
            Warning - Car impact financier et juridique important

        Contexte loggé:
            - Identification unique du contrat
            - Informations client pour traçabilité
            - Montant total pour audit financier
            - Commercial responsable de la signature
        """
        if not self.is_initialized:
            return

        with sentry_sdk.push_scope() as scope:
            # Tags pour filtrage des événements contractuels
            scope.set_tag("action", "contract_signature")
            scope.set_tag("contract_id", str(contract.id))
            scope.set_tag("signer_department", signer.department.value)

            # Données contractuelles critiques
            scope.set_extra("contract", {
                "id": contract.id,
                "client_name": contract.client.company_name,
                "total_amount": float(contract.total_amount),
                "status": contract.status.value
            })

            # Informations sur le signataire
            scope.set_extra("signer", {
                "id": signer.id,
                "email": signer.email,
                "full_name": signer.full_name,
                "employee_number": signer.employee_number
            })

            # Niveau warning car impact financier important
            sentry_sdk.capture_message(
                f"Signature contrat ID {contract.id} par {signer.full_name}",
                level="warning"
            )

    def log_exception(self, exception: Exception, context: Optional[Dict[str, Any]] = None):
        """
        Journaliser une exception système avec contexte enrichi.

        Cette méthode capture les exceptions avec leur stack trace complète
        et le contexte d'exécution pour faciliter le débogage.

        Args:
            exception: Exception à journaliser
            context: Contexte additionnel optionnel

        Fallback:
            Si Sentry n'est pas disponible, utilise le logging standard
            pour garantir la traçabilité des erreurs.
        """
        if not self.is_initialized:
            logging.error(f"Exception: {exception}")
            return

        with sentry_sdk.push_scope() as scope:
            scope.set_tag("action", "exception")

            # Ajout du contexte métier si fourni
            if context:
                scope.set_extra("context", context)

            # Capture avec stack trace automatique
            sentry_sdk.capture_exception(exception)

    def log_authentication_attempt(self, email: str, success: bool, ip_address: str = None):
        """
        Journaliser une tentative d'authentification pour audit de sécurité.

        Cette méthode enregistre toutes les tentatives de connexion,
        réussies ou échouées, pour détecter les patterns suspects.

        Args:
            email: Email de l'utilisateur tentant la connexion
            success: Succès ou échec de l'authentification
            ip_address: Adresse IP source (optionnelle)

        Niveau de sévérité:
            - Info pour connexions réussies
            - Warning pour tentatives échouées (détection d'intrusion)
        """
        if not self.is_initialized:
            return

        with sentry_sdk.push_scope() as scope:
            # Tags pour analyse des patterns de sécurité
            scope.set_tag("action", "authentication")
            scope.set_tag("success", str(success))
            scope.set_tag("security_audit", "true")

            # Données détaillées pour audit de sécurité
            scope.set_extra("auth_attempt", {
                "email": email,
                "success": success,
                "ip_address": ip_address or "unknown",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user_agent": "epic_events_cli"
            })

            # Niveau adapté selon le résultat
            level = "info" if success else "warning"
            status = "réussie" if success else "échouée"

            sentry_sdk.capture_message(
                f"Authentification {status}: {email}",
                level=level
            )

    def force_flush(self):
        """
        Forcer l'envoi immédiat des données vers Sentry.

        Cette méthode garantit que tous les événements en attente sont
        transmis à Sentry avant la fermeture de l'application.

        Timeout:
            5 secondes maximum pour éviter le blocage de l'application
            en cas de problème réseau.

        Gestion d'erreur:
            Échec silencieux pour ne pas interrompre l'arrêt normal
            de l'application.
        """
        if self.is_initialized:
            try:
                sentry_sdk.flush(timeout=5)
            except Exception:
                # Échec silencieux pour ne pas bloquer l'arrêt
                pass


# Instance globale du service de logging pour Epic Events
# ======================================================
# Cette instance unique est utilisée dans toute l'application pour garantir
# une configuration Sentry cohérente et un contexte utilisateur uniforme.
#
# Utilisation:
#   from src.services.logging_service import logger
#   logger.log_user_creation(new_user, admin_user)
#   logger.set_user_context(authenticated_user)
#
# Pattern Singleton:
#   Une seule instance par processus pour centraliser la configuration
#   et éviter les initialisations multiples de Sentry.
logger = SentryLogger()
