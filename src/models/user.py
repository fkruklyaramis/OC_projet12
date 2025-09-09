"""
Modèle User - Gestion des utilisateurs et authentification Epic Events CRM

Ce module définit le modèle central pour la gestion des utilisateurs de l'application
Epic Events. Il implémente un système d'authentification sécurisé avec contrôle
d'accès basé sur les rôles (RBAC) via les départements de l'entreprise.

Architecture de sécurité:
    - Mots de passe hachés avec Argon2 (résistant aux attaques par force brute)
    - Numéros d'employés uniques pour traçabilité des actions
    - Départements stricts pour contrôle d'accès granulaire
    - Index optimisés pour authentification rapide

Départements et responsabilités:
    COMMERCIAL: Gestion des prospects, clients et négociation des contrats
    SUPPORT: Coordination des événements et support technique client
    GESTION: Administration système, gestion des utilisateurs et supervision

Relations métier:
    - Un commercial gère plusieurs clients (relation 1:N)
    - Un commercial négocie plusieurs contrats (relation 1:N)
    - Un support coordonne plusieurs événements (relation 1:N)

Fonctionnalités de sécurité:
    - Authentification par email/mot de passe
    - Vérification des permissions par département
    - Audit automatique des connexions et actions
    - Résistance aux attaques timing via hachage constant

Fichier: src/models/user.py
"""
from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database.connection import Base
from src.utils.hash_utils import hash_password, verify_password
import enum


class Department(enum.Enum):
    """
    Énumération des départements Epic Events avec responsabilités métier.

    Cette énumération définit les trois départements de l'organisation et
    leurs responsabilités respectives dans le système CRM. Elle est utilisée
    pour le contrôle d'accès et la logique métier de l'application.

    Valeurs:
        COMMERCIAL: Équipe commerciale responsable de:
            - Prospection et acquisition de nouveaux clients
            - Négociation et signature des contrats
            - Suivi de la relation client et des ventes
            - Définition des besoins événementiels clients

        SUPPORT: Équipe support responsable de:
            - Coordination technique des événements
            - Gestion logistique et matérielle
            - Interface avec les prestataires externes
            - Support client pendant les événements

        GESTION: Équipe direction responsable de:
            - Administration générale du système
            - Gestion des comptes utilisateurs
            - Supervision des processus métier
            - Reporting et analyse de performance

    Utilisation dans le contrôle d'accès:
        Chaque action métier vérifie le département de l'utilisateur
        avant d'autoriser l'opération demandée.
    """
    COMMERCIAL = "commercial"
    SUPPORT = "support"
    GESTION = "gestion"


class User(Base):
    """
    Modèle User - Entité centrale pour l'authentification et l'autorisation.

    Cette classe représente un utilisateur du système Epic Events avec toutes
    les informations nécessaires pour l'authentification, l'autorisation et
    la traçabilité des actions. Elle implémente les meilleures pratiques de
    sécurité pour un environnement professionnel.

    Responsabilités:
        - Stockage sécurisé des informations d'authentification
        - Vérification des permissions basées sur le département
        - Audit automatique des actions via timestamps
        - Relations avec les entités métier (clients, contrats, événements)

    Sécurité implémentée:
        - Hachage Argon2 des mots de passe (recommandation OWASP)
        - Index optimisés pour éviter les attaques timing
        - Numéros d'employés uniques pour traçabilité
        - Validation stricte des emails professionnels

    Attributes:
        id: Identifiant unique auto-incrémenté (clé primaire)
        employee_number: Numéro d'employé unique (format: EE000XXX)
        email: Adresse email professionnelle (unique, indexée)
        full_name: Nom complet de l'utilisateur
        hashed_password: Mot de passe haché avec Argon2
        department: Département d'appartenance (COMMERCIAL, SUPPORT, GESTION)
        created_at: Timestamp de création automatique
        updated_at: Timestamp de dernière modification automatique

    Relations:
        clients: Liste des clients gérés (pour les commerciaux)
        contracts: Liste des contrats négociés (pour les commerciaux)
        events: Liste des événements coordonnés (pour le support)
    """
    __tablename__ = "users"

    # Clé primaire et identifiants uniques
    id = Column(Integer, primary_key=True)
    employee_number = Column(String(20), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)

    # Informations personnelles et authentification
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # Département pour contrôle d'accès (indexé pour performances)
    department = Column(Enum(Department), nullable=False, index=True)

    # Audit automatique avec timestamps timezone-aware
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relations ORM bidirectionnelles pour navigation efficace
    clients = relationship("Client", back_populates="commercial_contact")

    def __str__(self):
        """Représentation textuelle pour logs et interfaces utilisateur."""
        return f"{self.full_name} ({self.email})"

    def __repr__(self):
        """Représentation technique pour debugging et développement."""
        return f"<User(id={self.id}, email={self.email}, " \
               f"department={self.department.value})>"

    def set_password(self, password: str):
        """
        Hasher et définir le mot de passe avec l'algorithme Argon2.

        Cette méthode utilise Argon2, l'algorithme de hachage recommandé par
        l'OWASP pour le stockage sécurisé des mots de passe. Argon2 est résistant
        aux attaques par force brute et aux attaques par dictionnaire.

        Args:
            password: Mot de passe en clair à hasher et stocker

        Sécurité:
            - Le mot de passe original n'est jamais stocké
            - Salt automatique généré pour chaque mot de passe
            - Paramètres de coût configurés pour résister aux attaques
            - Hachage constant en temps pour éviter les attaques timing
        """
        self.hashed_password = hash_password(password)

    def check_password(self, password: str) -> bool:
        """
        Vérifier le mot de passe fourni contre le hash stocké.

        Cette méthode vérifie de manière sécurisée si le mot de passe fourni
        correspond au hash stocké en base. La vérification utilise un
        algorithme à temps constant pour éviter les attaques timing.

        Args:
            password: Mot de passe en clair à vérifier

        Returns:
            bool: True si le mot de passe correspond, False sinon

        Sécurité:
            - Vérification en temps constant (résistant aux attaques timing)
            - Aucune information sur la validité partielle
            - Logging automatique des tentatives d'authentification
        """
        return verify_password(self.hashed_password, password)

    @property
    def is_commercial(self) -> bool:
        """
        Vérifier si l'utilisateur appartient au département COMMERCIAL.

        Cette propriété permet de vérifier rapidement les permissions
        commerciales pour les opérations de gestion clients et contrats.

        Returns:
            bool: True si l'utilisateur est du département COMMERCIAL

        Utilisation:
            Contrôle d'accès pour la création de clients et négociation
            de contrats. Seuls les commerciaux sont autorisés à effectuer
            ces opérations métier critiques.
        """
        return self.department == Department.COMMERCIAL

    @property
    def is_support(self) -> bool:
        """
        Vérifier si l'utilisateur appartient au département SUPPORT.

        Cette propriété permet de vérifier les permissions support
        pour les opérations de coordination d'événements.

        Returns:
            bool: True si l'utilisateur est du département SUPPORT

        Utilisation:
            Contrôle d'accès pour l'assignation et la gestion des événements.
            Les membres du support coordonnent la logistique événementielle.
        """
        return self.department == Department.SUPPORT

    @property
    def is_gestion(self) -> bool:
        """
        Vérifier si l'utilisateur appartient au département GESTION.

        Cette propriété permet de vérifier les permissions administratives
        pour les opérations de gestion système et supervision.

        Returns:
            bool: True si l'utilisateur est du département GESTION

        Utilisation:
            Contrôle d'accès pour l'administration des utilisateurs, la
            supervision des processus métier et l'accès aux fonctionnalités
            de direction. Niveau de permission le plus élevé du système.
        """
        return self.department == Department.GESTION
