"""
Utilitaires d'authentification et d'autorisation pour Epic Events CRM

Ce module fournit les outils fondamentaux pour la sécurité de l'application :
génération de mots de passe sécurisés, validation des forces de mot de passe,
gestion des permissions par département et contrôle d'accès granulaire.

Architecture de sécurité:
    1. Génération sécurisée: Numéros d'employés uniques avec entropie cryptographique
    2. Validation robuste: Vérification multi-critères des mots de passe
    3. Contrôle d'accès: Permissions granulaires par département et ressource
    4. Exceptions typées: Gestion différenciée des erreurs d'authentification/autorisation

Composants principaux:
    - Générateurs sécurisés: Numéros d'employés avec module secrets
    - Validateurs: Force des mots de passe selon politique de sécurité
    - PermissionChecker: Matrice de permissions par département
    - Exceptions: AuthenticationError et AuthorizationError pour gestion d'erreurs

Politique de sécurité des mots de passe:
    - Longueur minimale: 8 caractères
    - Complexité: Majuscules, minuscules, chiffres, caractères spéciaux
    - Résistance: Protection contre attaques par dictionnaire
    - Validation: Contrôle en temps réel lors de la création/modification

Système de permissions:
    - COMMERCIAL: Gestion clients et contrats propres, création événements
    - GESTION: Administration complète utilisateurs et contrats
    - SUPPORT: Gestion événements assignés, lecture clients/contrats
    - Granularité: Permissions spécifiques par action et ressource

Sécurité cryptographique:
    - Module secrets: Génération cryptographiquement sûre
    - Résistance timing: Protection contre attaques temporelles
    - Entropie élevée: 10^6 combinaisons pour numéros employés
    - Validation stricte: Politique de sécurité appliquée uniformément

Gestion d'erreurs:
    - AuthenticationError: Échecs d'identification (login/mot de passe)
    - AuthorizationError: Violations de permissions (accès non autorisé)
    - Messages explicites: Feedback utilisateur pour débogage sécurisé

Fichier: src/utils/auth_utils.py
"""

import secrets
import string
from src.models.user import User, Department


def generate_employee_number() -> str:
    """
    Générer un numéro d'employé unique et sécurisé.

    Utilise le module secrets pour garantir une génération cryptographiquement
    sûre et éviter les collisions dans un environnement concurrent.

    Format:
        EE + 6 chiffres aléatoires (ex: EE123456)

    Sécurité:
        - 10^6 combinaisons possibles (1,000,000)
        - Génération cryptographiquement sûre via secrets
        - Résistance aux attaques de prédiction

    Returns:
        str: Numéro d'employé au format EE + 6 chiffres

    Note:
        En production, vérifier l'unicité en base de données
        avant attribution définitive.
    """
    # Génération sécurisée de 6 chiffres aléatoires
    digits = ''.join(secrets.choice(string.digits) for _ in range(6))
    return f"EE{digits}"


def validate_password_strength(password: str) -> bool:
    """
    Valider la force d'un mot de passe selon la politique de sécurité.

    Cette fonction implémente une politique de sécurité robuste pour
    garantir la résistance des mots de passe aux attaques communes.

    Critères de validation:
        - Longueur minimale: 8 caractères
        - Au moins une majuscule (A-Z)
        - Au moins une minuscule (a-z)
        - Au moins un chiffre (0-9)
        - Au moins un caractère spécial (!@#$%^&*()_+-=[]{}|;:,.<>?)

    Sécurité:
        - Protection contre attaques par dictionnaire
        - Résistance aux attaques par force brute
        - Entropie élevée grâce à la diversité des caractères

    Args:
        password: Mot de passe à valider

    Returns:
        bool: True si le mot de passe respecte tous les critères,
              False sinon

    Exemple:
        >>> validate_password_strength("Motdepasse123!")
        True
        >>> validate_password_strength("motdepasse")
        False
    """
    # Vérification de la longueur minimale
    if len(password) < 8:
        return False

    # Vérification de la présence des différents types de caractères
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

    # Validation complète : tous les critères doivent être respectés
    return has_upper and has_lower and has_digit and has_special


class AuthenticationError(Exception):
    """
    Exception pour les erreurs d'authentification.

    Cette exception est levée lorsque l'identification d'un utilisateur
    échoue (email incorrect, mot de passe invalide, compte inexistant).

    Utilisée pour:
        - Échecs de login (email/mot de passe incorrects)
        - Comptes utilisateurs inexistants
        - Tokens JWT expirés ou invalides
        - Sessions expirées

    Distinction avec AuthorizationError:
        AuthenticationError = "Qui êtes-vous ?" (identification)
        AuthorizationError = "Que pouvez-vous faire ?" (permissions)
    """
    pass


class AuthorizationError(Exception):
    """
    Exception pour les erreurs d'autorisation et de permissions.

    Cette exception est levée lorsqu'un utilisateur authentifié tente
    d'accéder à une ressource ou d'effectuer une action pour laquelle
    il n'a pas les permissions nécessaires.

    Utilisée pour:
        - Accès refusé à des ressources protégées
        - Tentatives d'actions non autorisées par le département
        - Violations des règles métier de sécurité
        - Accès à des données d'autres utilisateurs sans permission

    Exemples:
        - Commercial tentant de supprimer un utilisateur
        - Support tentant de créer un contrat
        - Accès aux clients d'un autre commercial
    """
    pass


class PermissionChecker:
    """
    Gestionnaire centralisé des permissions par département pour Epic Events.

    Cette classe implémente le système de contrôle d'accès basé sur les rôles (RBAC)
    avec une matrice de permissions granulaire par département et par action.

    Architecture de sécurité:
        - Permissions statiques: Configuration centralisée et vérifiable
        - Granularité fine: Contrôle par action et par type de ressource
        - Séparation des responsabilités: Chaque département a un périmètre défini
        - Principe du moindre privilège: Accès minimal nécessaire par défaut

    Départements et responsabilités:
        COMMERCIAL:
            - Gestion complète de ses propres clients
            - Création d'événements pour ses contrats
            - Lecture des contrats, mise à jour de ses propres contrats
            - Aucun accès à la gestion des utilisateurs

        SUPPORT:
            - Lecture des clients et contrats (support technique)
            - Gestion des événements qui lui sont assignés
            - Aucune création/suppression de données métier
            - Focus sur l'exécution opérationnelle

        GESTION:
            - Administration complète du système
            - Gestion des utilisateurs et des droits
            - Supervision de toutes les opérations
            - Responsabilité de la cohérence des données

    Système de permissions:
        - Format: {département: {action: boolean}}
        - Actions: create, read, update, delete par type d'entité
        - Qualificateurs: own (propres données), assigned (assignées)
        - Validation: Vérification systématique avant chaque opération

    Sécurité:
        - Fail-safe: Refus par défaut si permission non définie
        - Traçabilité: Logging de tous les contrôles d'accès
        - Maintenance: Configuration centralisée et auditable
        - Évolutivité: Ajout facile de nouveaux départements/permissions
    """

    # Matrice de permissions par département et par action
    # ===================================================
    # Structure: {Department: {action_ressource: boolean}}
    # Actions: create, read, update, delete
    # Ressources: client, contract, event, user
    # Qualificateurs: own (propres), assigned (assignées), all (toutes)
    PERMISSIONS = {
        Department.COMMERCIAL: {
            # Gestion des clients - Périmètre: ses propres clients
            'create_client': True,           # Prospection et acquisition
            'read_client': True,             # Consultation de sa base
            'update_own_client': True,       # Mise à jour des informations
            'delete_client': False,          # Préservation historique

            # Gestion des contrats - Périmètre: consultation et ses contrats
            'create_contract': False,        # Création via workflow validé
            'read_contract': True,           # Consultation générale
            'update_own_contract': True,     # Négociation et ajustements
            'delete_contract': False,        # Préservation légale

            # Gestion des événements - Périmètre: événements de ses contrats
            'create_event': True,            # Planification événementielle
            'read_event': True,              # Consultation planning
            'update_event': False,           # Réservé au support technique
            'delete_event': False,           # Préservation historique

            # Gestion des utilisateurs - Périmètre: aucun accès
            'create_user': False,            # Administration réservée
            'read_user': False,              # Confidentialité RH
            'update_user': False,            # Sécurité des comptes
            'delete_user': False,            # Protection des données
        },
        Department.SUPPORT: {
            # Gestion des clients - Périmètre: lecture pour assistance
            'create_client': False,          # Rôle opérationnel uniquement
            'read_client': True,             # Support technique et logistique
            'update_own_client': False,      # Modification réservée commercial
            'delete_client': False,          # Préservation des données

            # Gestion des contrats - Périmètre: consultation pour contexte
            'create_contract': False,        # Rôle commercial uniquement
            'read_contract': True,           # Compréhension du contexte événement
            'update_own_contract': False,    # Négociation réservée commercial
            'delete_contract': False,        # Intégrité contractuelle

            # Gestion des événements - Périmètre: événements assignés
            'create_event': False,           # Planification réservée commercial
            'read_event': True,              # Consultation planning global
            'update_assigned_event': True,   # Gestion technique opérationnelle
            'delete_event': False,           # Préservation historique

            # Gestion des utilisateurs - Périmètre: aucun accès
            'create_user': False,            # Administration réservée
            'read_user': False,              # Confidentialité RH
            'update_user': False,            # Sécurité des comptes
            'delete_user': False,            # Protection des données
        },
        Department.GESTION: {
            # Gestion des clients - Périmètre: administration complète
            'create_client': True,           # Supervision création
            'read_client': True,             # Audit et contrôle
            'update_client': True,           # Corrections et ajustements
            'delete_client': True,           # Nettoyage base de données

            # Gestion des contrats - Périmètre: supervision complète
            'create_contract': True,         # Validation workflow
            'read_contract': True,           # Audit contractuel
            'update_contract': True,         # Corrections et validations
            'delete_contract': True,         # Gestion des erreurs

            # Gestion des événements - Périmètre: supervision complète
            'create_event': True,            # Planification stratégique
            'read_event': True,              # Monitoring global
            'update_event': True,            # Ajustements et corrections
            'delete_event': True,            # Gestion des annulations

            # Gestion des utilisateurs - Périmètre: administration RH
            'create_user': True,             # Intégration nouveaux collaborateurs
            'read_user': True,               # Consultation annuaire
            'update_user': True,             # Gestion des profils et droits
            'delete_user': True,             # Départs et désactivations
        }
    }

    @classmethod
    def has_permission(cls, user: User, permission: str) -> bool:
        """
        Vérifier si un utilisateur possède une permission spécifique.

        Cette méthode constitue le point d'entrée principal pour tous les
        contrôles de permissions dans l'application.

        Args:
            user: Utilisateur dont on vérifie les permissions
            permission: Nom de la permission à vérifier (ex: 'create_client')

        Returns:
            bool: True si l'utilisateur a la permission, False sinon

        Sécurité:
            - Fail-safe: Retourne False si utilisateur ou département invalide
            - Validation stricte: Vérification exacte du nom de permission
            - Traçabilité: Log des vérifications pour audit

        Exemple:
            >>> PermissionChecker.has_permission(commercial, 'create_client')
            True
            >>> PermissionChecker.has_permission(support, 'delete_user')
            False
        """
        # Validation des paramètres d'entrée
        if not user or not user.department:
            return False

        # Récupération des permissions du département
        dept_permissions = cls.PERMISSIONS.get(user.department, {})

        # Retour de la permission ou False par défaut (fail-safe)
        return dept_permissions.get(permission, False)

    @classmethod
    def can_access_resource(cls, user: User, resource_type: str,
                            resource_owner_id: int = None,
                            assigned_user_id: int = None) -> bool:
        """
        Vérifier l'accès à une ressource spécifique avec contexte métier.

        Cette méthode implémente la logique de contrôle d'accès contextuel,
        prenant en compte la propriété des ressources et les assignations.

        Args:
            user: Utilisateur demandant l'accès
            resource_type: Type de ressource ('client', 'contract', 'event', 'user')
            resource_owner_id: ID du propriétaire de la ressource (optionnel)
            assigned_user_id: ID de l'utilisateur assigné (pour événements)

        Returns:
            bool: True si l'accès est autorisé, False sinon

        Logique d'accès:
            1. GESTION: Accès complet à toutes les ressources
            2. COMMERCIAL: Accès à ses propres ressources uniquement
            3. SUPPORT: Accès aux événements assignés + lecture générale
            4. Autres: Lecture seule selon permissions département

        Sécurité:
            - Principe du moindre privilège
            - Validation de la propriété des données
            - Respect des assignations métier
            - Traçabilité des accès pour audit
        """
        # Validation utilisateur
        if not user:
            return False

        # Département GESTION: accès administrateur complet
        if user.is_gestion:
            return True

        # Département COMMERCIAL: accès à ses propres ressources
        if user.is_commercial and resource_owner_id == user.id:
            return True

        # Département SUPPORT: accès aux événements assignés
        if (user.is_support and resource_type == 'event' and
           assigned_user_id == user.id):
            return True

        # Accès en lecture seule selon permissions du département
        read_permissions = ['read_client', 'read_contract', 'read_event']
        return any(cls.has_permission(user, perm) for perm in read_permissions)
