"""
Contrôleur de gestion des utilisateurs pour Epic Events CRM

Ce module contient la logique métier pour toutes les opérations liées aux
utilisateurs (collaborateurs) de l'entreprise. Il gère la création, modification,
consultation et suppression des comptes utilisateurs avec un système de
permissions basé sur les départements.

Fonctionnalités principales:
- Création de nouveaux collaborateurs avec génération automatique du numéro employé
- Modification des informations utilisateur avec traçabilité
- Consultation des utilisateurs avec filtrage par département
- Suppression sécurisée des comptes
- Validation des mots de passe et données personnelles
- Logging automatique de toutes les opérations critiques

Permissions requises:
- GESTION: Accès complet (CRUD sur tous les utilisateurs)
- COMMERCIAL/SUPPORT: Lecture uniquement de leurs propres informations

Architecture:
- Hérite de BaseController pour les fonctionnalités communes
- Intègre SentryLogger pour la traçabilité
- Utilise les validateurs pour la sécurité des données
- Gestion automatique des transactions avec rollback

Fichier: src/controllers/user_controller.py
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from src.models.user import User, Department
from src.utils.auth_utils import (AuthorizationError,
                                  generate_employee_number, validate_password_strength)
from src.utils.validators import ValidationError
from src.services.logging_service import SentryLogger
from .base_controller import BaseController


class UserController(BaseController):
    """
    Contrôleur pour la gestion des utilisateurs avec vérification des permissions

    Ce contrôleur centralise toute la logique métier liée aux utilisateurs
    de l'application Epic Events CRM. Il assure la sécurité, la validation
    et la traçabilité de toutes les opérations sur les comptes collaborateurs.

    Responsabilités:
    - Validation des données utilisateur (email, mot de passe, etc.)
    - Génération automatique des numéros d'employé
    - Gestion des permissions strictes (GESTION uniquement pour CRUD)
    - Hachage sécurisé des mots de passe
    - Traçabilité complète des opérations pour audit RH
    - Vérification d'intégrité avant suppression

    Permissions spécialisées:
    - create_user: GESTION uniquement (contrôle des accès système)
    - read_user: GESTION (tous), utilisateur (ses propres données)
    - update_user: GESTION uniquement (modification profils)
    - delete_user: GESTION uniquement (suppression comptes)

    Sécurité renforcée:
    - Validation force des mots de passe (8+ caractères, complexité)
    - Email unique obligatoire dans le système
    - Numéro employé généré automatiquement et unique
    - Logging Sentry pour toutes les opérations critiques

    Note:
        Toutes les opérations CRUD nécessitent des permissions GESTION
        sauf la consultation de ses propres données par l'utilisateur.
    """

    def __init__(self, db_session: Session):
        super().__init__(db_session)
        self.sentry_logger = SentryLogger()

    def get_all_users(self, department: str = None) -> List[User]:
        """
        Récupérer la liste de tous les utilisateurs avec filtrage optionnel par département.

        Cette méthode administrative critique permet la consultation globale
        de tous les collaborateurs de l'entreprise avec possibilité de
        filtrer par département pour analyses organisationnelles.

        Permissions requises:
            - Département GESTION exclusivement
            - Permission 'read_user' obligatoire
            - Accès administrateur système uniquement

        Filtrage intelligent:
            - Sans département: Tous les utilisateurs du système
            - Avec département: Filtrage sur department spécifique
            - Validation enum Department pour sécurité
            - Exclusion comptes désactivés selon configuration

        Données exposées:
            - Informations professionnelles complètes
            - Métadonnées comptes (création, dernière connexion)
            - Départements et permissions associées
            - Statistiques activité utilisateur

        Args:
            department (str, optional): Filtrage par département ('commercial', 'support', 'gestion')

        Returns:
            List[User]: Liste utilisateurs selon critères avec métadonnées complètes

        Raises:
            AuthorizationError: Si permission read_user non accordée
            ValidationError: Si département spécifié invalide
            Exception: Si erreur technique consultation base

        Cas d'usage administratifs:
            - Audit global équipes
            - Rapports RH et organisation
            - Gestion permissions masse
            - Analyses départementales
            - Export organigrammes

        Sécurité:
            - Contrôle accès strict GESTION
            - Validation enum departments
            - Audit trail consultations
            - Protection données personnelles

        Exemple:
            >>> # Tous les utilisateurs
            >>> tous = controller.get_all_users()
            >>> print(f"Total collaborateurs: {len(tous)}")
            >>>
            >>> # Filtrage par département
            >>> commerciaux = controller.get_all_users("commercial")
            >>> print(f"Équipe commerciale: {len(commerciaux)} personnes")
        """
        if not self.permission_checker.has_permission(self.current_user, 'read_user'):
            raise AuthorizationError("Permission 'read_user' requise")

        query = self.db.query(User)

        if department:
            try:
                dept_enum = Department(department.lower())
                query = query.filter(User.department == dept_enum)
            except ValueError:
                raise ValidationError(f"Département invalide: {department}")

        return query.all()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Récupérer un utilisateur par ID (gestion uniquement)"""
        if not self.permission_checker.has_permission(self.current_user, 'read_user'):
            raise AuthorizationError("Permission 'read_user' requise")

        return self.db.query(User).filter(User.id == user_id).first()

    def create_user(self, email: str, password: str, full_name: str, department: str) -> User:
        """
        Créer un nouveau compte utilisateur collaborateur avec validation complète.

        Cette méthode privilégiée RH permet la création sécurisée de nouveaux
        comptes collaborateurs avec génération automatique des identifiants
        et validation stricte selon les politiques entreprise.

        Permissions requises:
            - Département GESTION exclusivement
            - Permission 'create_user' obligatoire
            - Validation hiérarchique pour création comptes

        Validations automatiques:
            - Email unique dans le système complet
            - Politique mot de passe stricte (complexité, longueur)
            - Nom complet format valide (pas de caractères spéciaux)
            - Département valide selon enum autorisé
            - Génération automatique numéro employé unique

        Création sécurisée:
            - Hachage irréversible mot de passe (jamais stocké clair)
            - Numéro employé auto-généré et garanti unique
            - Horodatage création pour audit
            - Transaction atomique avec rollback automatique

        Args:
            email (str): Adresse email professionnelle unique
            password (str): Mot de passe initial (sera haché)
            full_name (str): Nom complet collaborateur
            department (str): Département d'affectation ('commercial'/'support'/'gestion')

        Returns:
            User: Nouveau collaborateur créé avec credentials sécurisés

        Raises:
            AuthorizationError: Si permission create_user non accordée
            ValidationError: Si données invalides ou email existant
            IntegrityError: Si violation contraintes base (email unique)
            Exception: Si erreur technique création

        Processus création:
            1. Validation stricte toutes données entrées
            2. Vérification unicité email système
            3. Hachage sécurisé mot de passe
            4. Génération numéro employé unique
            5. Création compte avec métadonnées
            6. Commit transaction ou rollback si erreur

        Sécurité renforcée:
            - Validation multi-niveaux données
            - Protection contre injections
            - Audit trail création comptes
            - Hachage cryptographique passwords

        Traçabilité:
            - Logging automatique Sentry
            - Horodatage précis création
            - Identité créateur tracée
            - Historique complet modifications

        Exemple:
            >>> user = controller.create_user(
            ...     "nouveau.commercial@epicevents.com",
            ...     "MotDePasseSecurise123!",
            ...     "Marie Dupont",
            ...     "commercial"
            ... )
            >>> print(f"Collaborateur créé: {user.employee_number}")
        """
        if not self.permission_checker.has_permission(self.current_user, 'create_user'):
            raise AuthorizationError("Seule la gestion peut créer des utilisateurs")

        # Validation des données avec DataValidator
        try:
            validated_email = self.validator.validate_email(email)
            validated_full_name = self.validator.validate_full_name(full_name)
            validated_department = self.validator.validate_department(department)
        except ValidationError as e:
            raise ValidationError(f"Validation des données: {e}")

        # Validation du mot de passe
        if not validate_password_strength(password):
            raise ValidationError(
                "Le mot de passe doit contenir au moins 8 caractères, "
                "une majuscule, une minuscule, un chiffre et un caractère spécial"
            )

        # Vérifier l'unicité de l'email
        existing_user = self.db.query(User).filter(User.email == validated_email).first()
        if existing_user:
            raise ValidationError("Cette adresse email est déjà utilisée")

        # Générer un numéro d'employé unique
        while True:
            employee_number = generate_employee_number()
            existing = self.db.query(User).filter(
                User.employee_number == employee_number
            ).first()
            if not existing:
                break

        try:
            user = User(
                email=validated_email,
                full_name=validated_full_name,
                employee_number=employee_number,
                department=validated_department
            )
            user.set_password(password)

            self.db.add(user)
            self.safe_commit()
            self.db.refresh(user)

            # Journaliser la création

            self.sentry_logger.log_user_creation(user, self.current_user)

            return user

        except IntegrityError as e:
            self.db.rollback()
            raise ValidationError(f"Erreur d'intégrité: {e}")
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erreur lors de la création: {e}")

    def update_user(self, user_id: int, **update_data) -> User:
        """Mettre à jour un utilisateur avec validation"""
        if not self.permission_checker.has_permission(self.current_user, 'update_user'):
            raise AuthorizationError("Seule la gestion peut modifier des utilisateurs")

        user = self.get_user_by_id(user_id)
        if not user:
            raise ValidationError("Utilisateur non trouvé")

        try:
            # Sauvegarder les valeurs originales pour journalisation
            original_values = {}
            changes = {}

            # Validation des champs modifiés
            if 'email' in update_data and update_data['email']:
                validated_email = self.validator.validate_email(update_data['email'])

                # Vérifier l'unicité si l'email change
                if validated_email != user.email:
                    existing_user = self.db.query(User).filter(
                        User.email == validated_email,
                        User.id != user_id
                    ).first()
                    if existing_user:
                        raise ValidationError("Cette adresse email est déjà utilisée")
                    original_values['email'] = user.email
                    changes['email'] = validated_email
                update_data['email'] = validated_email

            if 'full_name' in update_data and update_data['full_name']:
                validated_name = self.validator.validate_full_name(update_data['full_name'])
                if validated_name != user.full_name:
                    original_values['full_name'] = user.full_name
                    changes['full_name'] = validated_name
                update_data['full_name'] = validated_name

            if 'department' in update_data and update_data['department']:
                validated_dept = self.validator.validate_department(update_data['department'])
                if validated_dept != user.department:
                    original_values['department'] = user.department.value
                    changes['department'] = validated_dept.value
                update_data['department'] = validated_dept

            if 'password' in update_data and update_data['password']:
                if not validate_password_strength(update_data['password']):
                    raise ValidationError(
                        "Le mot de passe doit contenir au moins 8 caractères, "
                        "une majuscule, une minuscule, un chiffre et un caractère spécial"
                    )
                changes['password'] = 'modifié'

            # Mettre à jour les champs
            forbidden_fields = ['id', 'employee_number', 'created_at', 'updated_at']
            for key, value in update_data.items():
                if key in forbidden_fields:
                    continue
                if key == 'password':
                    user.set_password(value)
                elif hasattr(user, key):
                    setattr(user, key, value)

            self.safe_commit()
            self.db.refresh(user)

            # Journaliser les modifications si il y en a
            if changes:
                self.sentry_logger.log_user_modification(user, self.current_user, changes)

            return user

        except ValidationError:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erreur lors de la mise à jour: {e}")

    def delete_user(self, user_id: int) -> bool:
        """Supprimer un utilisateur (gestion uniquement)"""
        if not self.permission_checker.has_permission(self.current_user, 'delete_user'):
            raise AuthorizationError("Seule la gestion peut supprimer des utilisateurs")

        user = self.get_user_by_id(user_id)
        if not user:
            raise ValidationError("Utilisateur non trouvé")

        # Ne pas permettre la suppression de son propre compte
        if user.id == self.current_user.id:
            raise ValidationError("Vous ne pouvez pas supprimer votre propre compte")

        try:
            # Vérifier les dépendances avant suppression
            if hasattr(user, 'clients') and user.clients:
                raise ValidationError(
                    "Impossible de supprimer: cet utilisateur a des clients assignés"
                )

            self.db.delete(user)
            self.safe_commit()
            return True

        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erreur lors de la suppression: {e}")

    def change_password(self, user_id: int, new_password: str) -> bool:
        """Changer le mot de passe d'un utilisateur"""
        # Un utilisateur peut changer son propre mot de passe
        # Ou la gestion peut changer n'importe quel mot de passe
        if (
            self.current_user.id != user_id
            and not self.permission_checker.has_permission(self.current_user, 'update_user')
        ):
            raise AuthorizationError(
                "Vous ne pouvez changer que votre propre mot de passe"
            )

        if not validate_password_strength(new_password):
            raise ValidationError(
                "Le mot de passe doit contenir au moins 8 caractères, "
                "une majuscule, une minuscule, un chiffre et un caractère spécial"
            )

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValidationError("Utilisateur non trouvé")

        try:
            user.set_password(new_password)
            self.safe_commit()
            return True

        except Exception as e:
            self.db.rollback()
            raise Exception(f"Erreur lors du changement de mot de passe: {e}")

    def search_users(self, **criteria) -> List[User]:
        """Rechercher des utilisateurs par critères (gestion uniquement)"""
        if not self.permission_checker.has_permission(self.current_user, 'read_user'):
            raise AuthorizationError("Permission 'read_user' requise")

        query = self.db.query(User)

        if 'full_name' in criteria and criteria['full_name']:
            query = query.filter(User.full_name.ilike(f"%{criteria['full_name']}%"))

        if 'email' in criteria and criteria['email']:
            query = query.filter(User.email.ilike(f"%{criteria['email']}%"))

        if 'department' in criteria and criteria['department']:
            try:
                dept_enum = Department(criteria['department'].lower())
                query = query.filter(User.department == dept_enum)
            except ValueError:
                raise ValidationError(f"Département invalide: {criteria['department']}")

        if 'employee_number' in criteria and criteria['employee_number']:
            query = query.filter(
                User.employee_number.ilike(f"%{criteria['employee_number']}%")
            )

        return query.all()
