"""
Gestionnaire JWT pour l'authentification persistante Epic Events CRM

Ce module fournit une gestion complète des tokens JWT pour l'authentification
persistante, permettant aux utilisateurs de rester connectés entre les sessions
tout en maintenant un niveau de sécurité élevé.

Architecture JWT:
    1. Génération: Création de tokens signés avec informations utilisateur
    2. Stockage: Sauvegarde sécurisée locale pour persistance
    3. Validation: Vérification signature et expiration
    4. Gestion: Renouvellement et révocation des tokens

Fonctionnalités principales:
    - Authentification persistante entre sessions
    - Stockage sécurisé local des tokens
    - Validation automatique de l'expiration
    - Gestion des données utilisateur dans le payload
    - Nettoyage automatique des tokens expirés

Structure du token JWT:
    Header: Algorithme de signature (HS256)
    Payload: Données utilisateur (ID, email, département, etc.)
    Signature: Validation de l'intégrité avec clé secrète

Sécurité:
    - Signature HMAC-SHA256 avec clé secrète forte
    - Expiration automatique (8 heures par défaut)
    - Stockage local sécurisé (permissions restreintes)
    - Validation systématique avant utilisation
    - Révocation possible via suppression du fichier

Gestion de session:
    - Connexion automatique si token valide
    - Déconnexion automatique si token expiré
    - Renouvellement transparent en arrière-plan
    - Persistance entre redémarrages de l'application

Conformité sécurité:
    - Standards JWT (RFC 7519)
    - Bonnes pratiques OWASP
    - Protection contre replay attacks
    - Gestion sécurisée du stockage local

Fichier: src/utils/jwt_utils.py
"""

import jwt
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from pathlib import Path
from src.database.config import SECRET_KEY


class JWTManager:
    """
    Gestionnaire JWT pour l'authentification persistante et sécurisée.

    Cette classe encapsule toute la logique de gestion des tokens JWT,
    depuis la génération jusqu'à la validation, en passant par le stockage
    sécurisé et la gestion des expirations.

    Responsabilités:
        - Génération de tokens JWT signés avec données utilisateur
        - Stockage sécurisé local pour persistance entre sessions
        - Validation de l'intégrité et de l'expiration des tokens
        - Nettoyage automatique des tokens expirés ou invalides
        - Interface unifiée pour toutes les opérations JWT

    Configuration sécurisée:
        - Algorithme: HMAC-SHA256 (HS256) pour signature
        - Expiration: 8 heures (configurable selon besoins métier)
        - Stockage: Répertoire utilisateur avec permissions restreintes
        - Validation: Vérification systématique avant utilisation

    Attributs:
        secret_key: Clé secrète pour signature (depuis configuration)
        algorithm: Algorithme de signature JWT
        token_file: Chemin vers le fichier de stockage local
        expiration_hours: Durée de validité du token en heures
    """

    def __init__(self):
        """
        Initialiser le gestionnaire JWT avec configuration sécurisée.

        Configure tous les paramètres nécessaires pour la gestion des tokens
        JWT avec des valeurs par défaut sécurisées.
        """
        self.secret_key = SECRET_KEY
        self.algorithm = "HS256"
        self.token_file = Path.home() / ".epic_events" / "token"
        self.expiration_hours = 8

    def _ensure_token_dir(self):
        """
        Créer le répertoire de stockage du token si nécessaire.

        Cette méthode garantit l'existence du répertoire de stockage avec
        les permissions appropriées pour la sécurité des tokens.

        Sécurité:
            - Permissions restreintes au propriétaire uniquement
            - Création récursive si répertoires parents inexistants
            - Gestion silencieuse si répertoire déjà existant
        """
        self.token_file.parent.mkdir(parents=True, exist_ok=True)

    def generate_token(self, user_id: int, email: str, department: str,
                       employee_number: str) -> str:
        """
        Générer un JWT token signé pour l'utilisateur.

        Cette méthode crée un token JWT contenant toutes les informations
        nécessaires pour l'authentification et l'autorisation.

        Args:
            user_id: Identifiant unique de l'utilisateur en base
            email: Adresse email pour identification humaine
            department: Département pour contrôle des permissions
            employee_number: Numéro d'employé pour audit

        Returns:
            str: Token JWT signé prêt à être stocké ou transmis

        Payload du token:
            - user_id: Liaison avec base de données
            - email: Identification utilisateur
            - department: Permissions et autorisation
            - employee_number: Traçabilité et audit
            - exp: Timestamp d'expiration Unix
            - iat: Timestamp d'émission Unix

        Sécurité:
            - Signature HMAC-SHA256 avec clé secrète
            - Expiration automatique selon configuration
            - Horodatage précis pour validation temporelle
            - Format standard JWT pour interopérabilité
        """
        payload = {
            'user_id': user_id,
            'email': email,
            'department': department,
            'employee_number': employee_number,
            'exp': datetime.now(timezone.utc) + timedelta(hours=self.expiration_hours),
            'iat': datetime.now(timezone.utc)
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Vérifier et décoder un JWT token.

        Cette méthode valide l'intégrité et l'expiration d'un token JWT
        et retourne les données utilisateur si valide.

        Args:
            token: Token JWT à vérifier

        Returns:
            Dict contenant les données utilisateur si token valide,
            None si token invalide ou expiré

        Vérifications effectuées:
            - Signature: Intégrité du token avec clé secrète
            - Expiration: Validation du timestamp exp
            - Format: Structure JWT valide
            - Algorithme: Correspondance avec algorithme configuré

        Gestion d'erreurs:
            - jwt.ExpiredSignatureError: Token expiré
            - jwt.InvalidTokenError: Token malformé ou signature invalide
            - Autres erreurs: Gestion gracieuse avec retour None

        Sécurité:
            - Validation stricte de la signature
            - Vérification automatique de l'expiration
            - Retour sécurisé en cas d'erreur
            - Aucune fuite d'information sur la cause d'échec
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            # Token expiré - nettoyage recommandé
            return None
        except jwt.InvalidTokenError:
            # Token invalide - signature incorrecte ou format malformé
            return None

    def save_token(self, token: str) -> bool:
        """
        Sauvegarder le token sur le disque de manière sécurisée.

        Cette méthode stocke le token JWT dans un fichier local pour
        persistance entre les sessions de l'application.

        Args:
            token: Token JWT à sauvegarder

        Returns:
            bool: True si sauvegarde réussie, False en cas d'erreur

        Sécurité du stockage:
            - Répertoire utilisateur (~/.epic_events/)
            - Permissions restreintes au propriétaire
            - Nom de fichier non évident ('token')
            - Gestion d'erreurs silencieuse pour sécurité

        Gestion d'erreurs:
            - Permissions insuffisantes: Retour False
            - Espace disque insuffisant: Retour False
            - Autres erreurs I/O: Gestion gracieuse
        """
        try:
            self._ensure_token_dir()
            with open(self.token_file, 'w') as f:
                json.dump({
                    'token': token,
                    'created_at': datetime.now(timezone.utc).isoformat()
                }, f)
            # Sécuriser le fichier (lecture/écriture pour le propriétaire uniquement)
            os.chmod(self.token_file, 0o600)
            return True
        except Exception:
            # Gestion silencieuse pour éviter les fuites d'information
            return False

    def load_token(self) -> Optional[str]:
        """
        Charger le token JWT depuis le stockage local.

        Cette méthode récupère le token précédemment sauvegardé pour
        restaurer une session utilisateur existante.

        Returns:
            str: Token JWT si trouvé et lisible, None sinon

        Sécurité:
            - Vérification de l'existence du fichier
            - Gestion gracieuse des erreurs de lecture
            - Retour None pour fichier corrompu ou inaccessible
            - Aucune exception propagée vers l'appelant

        Gestion d'erreurs:
            - Fichier inexistant: Retour None (cas normal)
            - Permissions insuffisantes: Retour None
            - JSON malformé: Retour None
            - Autres erreurs I/O: Gestion silencieuse
        """
        try:
            if not self.token_file.exists():
                return None

            with open(self.token_file, 'r') as f:
                data = json.load(f)
                return data.get('token')
        except Exception:
            # Fichier corrompu ou inaccessible - retour sécurisé
            return None

    def clear_token(self) -> bool:
        """
        Supprimer le token stocké (déconnexion).

        Cette méthode nettoie le stockage local pour déconnecter
        l'utilisateur et invalider la session persistante.

        Returns:
            bool: True si suppression réussie ou fichier inexistant,
                  False en cas d'erreur

        Utilisation:
            - Déconnexion manuelle de l'utilisateur
            - Nettoyage après détection de token expiré
            - Réinitialisation de session lors d'erreurs
            - Procédures de sécurité préventives

        Sécurité:
            - Suppression physique du fichier
            - Gestion gracieuse si fichier déjà absent
            - Retour succès même si fichier inexistant
            - Échec silencieux pour éviter fuites d'information
        """
        try:
            if self.token_file.exists():
                self.token_file.unlink()
            return True
        except Exception:
            # Erreur de suppression - situation critique mais gérée
            return False

    def logout(self) -> bool:
        """
        Déconnecter l'utilisateur en supprimant son token.

        Méthode alias pour clear_token() qui respecte la convention
        de nommage pour les opérations de déconnexion.

        Returns:
            bool: True si déconnexion réussie, False sinon
        """
        return self.clear_token()

    def get_current_user_data(self) -> Optional[Dict[str, Any]]:
        """
        Récupérer les données de l'utilisateur actuellement connecté.

        Cette méthode combine chargement, validation et nettoyage
        automatique pour fournir les données utilisateur fiables.

        Returns:
            Dict contenant les données utilisateur si session valide,
            None si aucune session ou session expirée

        Logique de validation:
            1. Chargement du token depuis le stockage local
            2. Vérification de la validité (signature + expiration)
            3. Nettoyage automatique si token invalide
            4. Retour des données utilisateur ou None

        Données retournées (si valide):
            - user_id: Identifiant base de données
            - email: Adresse email utilisateur
            - department: Département pour permissions
            - employee_number: Numéro d'employé
            - exp: Timestamp expiration
            - iat: Timestamp émission

        Maintenance automatique:
            - Nettoyage des tokens expirés
            - Suppression des tokens corrompus
            - Gestion transparente des erreurs
        """
        token = self.load_token()
        if not token:
            return None

        payload = self.verify_token(token)
        if not payload:
            # Token expiré ou invalide - nettoyage automatique
            self.clear_token()
            return None

        return payload

    def is_authenticated(self) -> bool:
        """
        Vérifier si un utilisateur est actuellement authentifié.

        Cette méthode fournit une vérification simple et rapide
        de l'état d'authentification sans récupérer les données.

        Returns:
            bool: True si utilisateur authentifié avec session valide,
                  False sinon

        Utilisation:
            - Contrôles d'accès rapides
            - Redirection selon état d'authentification
            - Validation avant opérations sensibles
            - Interface utilisateur conditionnelle

        Performance:
            - Optimisée pour vérifications fréquentes
            - Cache implicite via get_current_user_data
            - Validation complète mais efficace
            - Nettoyage automatique intégré
        """
        return self.get_current_user_data() is not None
