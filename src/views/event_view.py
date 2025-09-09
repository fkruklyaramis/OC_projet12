"""
Vue de gestion des événements pour Epic Events CRM

Ce module fournit l'interface utilisateur pour la planification, l'organisation
et le suivi des événements avec gestion des assignations support, validation
des dates et coordination entre départements.

Fonctionnalités événementielles:
    - Création d'événements liés aux contrats signés
    - Planification avec validation des dates et durées
    - Assignation du personnel support technique
    - Suivi de l'exécution et des modifications
    - Gestion des participants et logistique

Coordination inter-départements:
    - COMMERCIAL: Création d'événements pour leurs contrats
    - SUPPORT: Gestion technique des événements assignés
    - GESTION: Administration complète et assignations

Interface de planification:
    - Calendrier avec affichage des événements à venir
    - Formulaires de création avec validation temporelle
    - Tables de suivi avec statuts et assignations
    - Filtrage par date, support ou statut

Gestion logistique:
    - Validation des capacités et contraintes lieu
    - Suivi du nombre de participants
    - Coordination des équipes support
    - Notes et commentaires pour organisation

Fichier: src/views/event_view.py
"""

from typing import List
from src.controllers.event_controller import EventController
from src.models.event import Event
from src.utils.auth_utils import AuthenticationError, AuthorizationError
from src.config.messages import EVENT_MESSAGES, VALIDATION_MESSAGES
from .base_view import BaseView


class EventView(BaseView):
    """
    Vue spécialisée pour la gestion des événements Epic Events.

    Cette classe fournit une interface complète pour la planification,
    l'organisation et le suivi des événements avec coordination
    entre les départements commercial, support et gestion.

    Responsabilités événementielles:
        - Interface de création et planification
        - Gestion des assignations support technique
        - Suivi de l'exécution et modifications
        - Coordination logistique et ressources
        - Validation des contraintes temporelles

    Workflow événementiel:
        - Création: Basée sur contrats signés
        - Planification: Dates, lieu, participants
        - Assignation: Personnel support technique
        - Exécution: Suivi temps réel
        - Clôture: Bilan et feedback

    Interface de coordination:
        - Vue calendaire des événements
        - Tables avec assignations et statuts
        - Formulaires de modification dynamiques
        - Notifications et alertes planning
        - Rapports de suivi et statistiques
    """

    def __init__(self):
        """
        Initialiser la vue de gestion des événements.

        Configure le contrôleur événement avec session DB
        et permissions selon département utilisateur.
        """
        super().__init__()
        self.event_controller = self.setup_controller(EventController)

    def list_all_events_command(self):
        """
        Afficher la liste complète des événements (supervision).

        Cette méthode présente tous les événements du système avec
        informations de planification et assignations support.

        Restrictions d'accès:
            - Réservé au département GESTION
            - Vue globale pour supervision
            - Permissions administratives requises

        Affichage superviseur:
            - Liste chronologique des événements
            - Statuts et assignations support
            - Informations contrat et client associés
            - Dates et contraintes logistiques
            - Indicateurs de charge et planning
        """
        try:
            # Authentification et configuration des permissions utilisateur
            current_user = self.auth_service.require_authentication()
            self.event_controller.set_current_user(current_user)

            # Récupération sécurisée de tous les événements système
            events = self.event_controller.get_all_events()

            self.display_info(EVENT_MESSAGES["all_events_header"])

            if not events:
                # Aucun événement planifié dans le système
                self.display_info(EVENT_MESSAGES["no_events_found"])
                return

            # Affichage du tableau de supervision avec données complètes
            self._display_events_table(events)

        except (AuthenticationError, AuthorizationError) as e:
            # Gestion des erreurs d'accès et d'authentification
            self.display_error(VALIDATION_MESSAGES["authorization_error"].format(error=e))
        except Exception as e:
            # Gestion des erreurs système inattendues
            self.display_error(VALIDATION_MESSAGES["general_error"].format(error=e))

    def list_my_events_command(self):
        """
        Afficher les événements assignés à l'utilisateur connecté.

        Cette méthode présente la liste personnalisée des événements
        selon le département et les responsabilités de l'utilisateur.

        Logique d'affichage par département:
            - COMMERCIAL: Événements de leurs contrats
            - SUPPORT: Événements assignés pour gestion technique
            - GESTION: Vue globale avec permissions complètes

        Interface personnalisée:
            - Filtrage automatique selon permissions
            - Vue centrée sur responsabilités utilisateur
            - Actions disponibles selon département
            - Priorités et échéances personnelles
            - Notifications et alertes contextuelles
        """
        try:
            current_user = self.auth_service.require_authentication()
            self.event_controller.set_current_user(current_user)

            events = self.event_controller.get_my_events()

            role_info = ""
            if current_user.is_support:
                role_info = " (ASSIGNES A MOI)"
            elif current_user.is_commercial:
                role_info = " (MES CONTRATS)"

            self.display_info(f"=== MES EVENEMENTS{role_info} ===")

            if not events:
                self.display_info(EVENT_MESSAGES["no_events_found"])
                return

            self._display_events_table(events)

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(VALIDATION_MESSAGES["authorization_error"].format(error=e))
        except Exception as e:
            self.display_error(VALIDATION_MESSAGES["general_error"].format(error=e))

    def create_event_command(self):
        """
        Créer un nouvel événement dans le système.

        Cette méthode guide l'utilisateur dans la création d'un événement
        avec validation des données et assignation selon permissions.

        Processus de création:
            - Sélection du contrat signé (requis)
            - Configuration dates et durée événement
            - Définition lieu et nombre participants
            - Assignation initiale personnel support
            - Validation contraintes et enregistrement

        Restrictions par département:
            - COMMERCIAL: Création pour leurs contrats uniquement
            - GESTION: Création libre avec assignation support
            - SUPPORT: Lecture seule, pas de création

        Validation événementielle:
            - Contrat doit être signé et valide
            - Dates cohérentes et dans le futur
            - Capacités lieu et ressources disponibles
            - Personnel support disponible aux dates
            - Données complètes et conformes
        """
        # Implementation de create_event_command sera dans le code suivant

    def list_upcoming_events_command(self, days_ahead: int = 30):
        """
        Afficher les événements à venir dans une période définie.

        Cette méthode présente la planification future des événements
        avec focus sur les échéances et préparatifs nécessaires.

        Paramètres de planification:
            - days_ahead: Horizon temporel (défaut 30 jours)
            - Filtrage automatique selon département
            - Vue chronologique des événements futurs

        Interface de planification:
            - Liste chronologique avec dates approchantes
            - Priorités selon échéances et préparatifs
            - Assignations support et responsabilités
            - Indicateurs de charge et disponibilités
            - Alertes pour événements critiques

        Utilité départementale:
            - SUPPORT: Événements assignés approchants
            - COMMERCIAL: Suivi événements clients
            - GESTION: Vue globale planification système
        """
        try:
            current_user = self.auth_service.require_authentication()
            self.event_controller.set_current_user(current_user)

            events = self.event_controller.get_upcoming_events(days_ahead)

            role_info = ""
            if current_user.is_support:
                role_info = " (MES ASSIGNATIONS)"
            elif current_user.is_commercial:
                role_info = " (MES CONTRATS)"

            self.display_info(f"=== EVENEMENTS A VENIR ({days_ahead} JOURS){role_info} ===")

            if not events:
                self.display_info(f"Aucun événement dans les {days_ahead} prochains jours")
                return

            self._display_events_table(events)

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(VALIDATION_MESSAGES["authorization_error"].format(error=e))
        except Exception as e:
            self.display_error(VALIDATION_MESSAGES["general_error"].format(error=e))

    def list_unassigned_events_command(self):
        """
        Afficher les événements sans personnel support assigné.

        Cette méthode présente la liste des événements nécessitant
        une assignation de personnel support technique.

        Fonctionnalité de gestion:
            - Réservée au département GESTION
            - Vue des événements orphelins sans support
            - Interface d'assignation et coordination
            - Priorisation selon dates et urgences

        Utilité organisationnelle:
            - Identification événements non couverts
            - Facilitation assignation personnel
            - Prévention oublis et conflits planning
            - Optimisation charge travail support
            - Garantie couverture événements système
        """
        try:
            current_user = self.auth_service.require_authentication()
            self.event_controller.set_current_user(current_user)

            events = self.event_controller.get_events_without_support()

            self.display_info(EVENT_MESSAGES["unassigned_header"])

            if not events:
                self.display_info(EVENT_MESSAGES["no_unassigned_events"])
                return

            self._display_events_table(events)

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(VALIDATION_MESSAGES["authorization_error"].format(error=e))
        except Exception as e:
            self.display_error(VALIDATION_MESSAGES["general_error"].format(error=e))

    def view_event_command(self, event_id: int):
        """
        Afficher les détails complets d'un événement spécifique.

        Cette méthode présente une vue détaillée d'un événement
        avec toutes les informations de planification et coordination.

        Informations détaillées affichées:
            - Données événement (nom, dates, lieu, participants)
            - Informations contrat et client associé
            - Personnel support assigné et coordonnées
            - Statut et avancement de la planification
            - Notes et commentaires de coordination

        Contrôle d'accès:
            - SUPPORT: Leurs événements assignés
            - COMMERCIAL: Événements de leurs contrats
            - GESTION: Accès complet tous événements

        Interface de consultation:
            - Présentation structurée avec Rich
            - Codes couleur selon statut
            - Actions disponibles selon permissions
            - Navigation vers modifications si autorisé
        """
        try:
            current_user = self.auth_service.require_authentication()
            self.event_controller.set_current_user(current_user)

            event = self.event_controller.get_event_by_id(event_id)
            if not event:
                self.display_error(EVENT_MESSAGES["not_found_or_access_denied"])
                return

            self._display_event_details(event)

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(VALIDATION_MESSAGES["authorization_error"].format(error=e))
        except Exception as e:
            self.display_error(VALIDATION_MESSAGES["general_error"].format(error=e))

    def search_events_command(self):
        """
        Rechercher des événements selon critères et permissions.

        Cette méthode fournit une interface de recherche avancée
        pour localiser des événements selon différents critères.

        Critères de recherche disponibles:
            - Recherche par nom d'événement
            - Filtrage par dates (période)
            - Recherche par client ou contrat
            - Filtrage par personnel support
            - Recherche par lieu ou statut

        Logique de permissions:
            - SUPPORT: Recherche dans leurs assignations
            - COMMERCIAL: Recherche dans leurs contrats
            - GESTION: Recherche globale système

        Interface de recherche:
            - Formulaire interactif avec critères multiples
            - Validation des saisies et dates
            - Affichage résultats avec pagination
            - Export et sauvegarde des recherches
            - Statistiques et synthèses des résultats
        """
        try:
            # Authentification et configuration permissions de recherche
            current_user = self.auth_service.require_authentication()
            self.event_controller.set_current_user(current_user)

            # Configuration interface selon département utilisateur
            role_info = ""
            if current_user.is_support:
                role_info = " (MES ASSIGNATIONS)"
            elif current_user.is_commercial:
                role_info = " (MES CONTRATS)"

            self.display_info(f"=== RECHERCHE D'EVENEMENTS{role_info} ===")

            # Construction interactive des critères de recherche
            criteria = {}

            # Critère nom événement
            name = self.get_user_input("Nom de l'événement (optionnel)")
            if name:
                criteria['name'] = name

            # Critère lieu événement
            location = self.get_user_input("Lieu (optionnel)")
            if location:
                criteria['location'] = location

            # Critère client associé
            client_name = self.get_user_input("Nom du client (optionnel)")
            if client_name:
                criteria['client_name'] = client_name

            # Critère date de début avec validation
            start_date_str = self.get_user_input("Date de début (YYYY-MM-DD, optionnel)")
            if start_date_str:
                try:
                    from datetime import datetime
                    criteria['start_date'] = datetime.strptime(start_date_str, '%Y-%m-%d')
                except ValueError:
                    self.display_error("Format de date invalide. Utilisez YYYY-MM-DD")
                    return

            # Validation présence critères de recherche
            if not criteria:
                self.display_info(EVENT_MESSAGES["no_search_criteria"])
                return

            # Exécution recherche avec critères validés
            events = self.event_controller.search_events(**criteria)

            if events:
                # Affichage résultats de recherche avec statistiques
                self.display_success(f"{len(events)} événement(s) trouvé(s)")
                self._display_events_table(events)
            else:
                # Aucun résultat pour critères spécifiés
                self.display_info(EVENT_MESSAGES["no_search_results"])

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(VALIDATION_MESSAGES["authorization_error"].format(error=e))
        except Exception as e:
            self.display_error(VALIDATION_MESSAGES["general_error"].format(error=e))

    def _display_event_details(self, event: Event):
        """Afficher les détails d'un événement"""
        print(f"\n=== EVENEMENT {event.id} ===")
        print(f"Nom: {event.name}")
        print(f"Lieu: {event.location}")
        print(f"Participants: {event.attendees}")
        print(f"Date début: {event.start_date.strftime('%Y-%m-%d %H:%M')}")
        print(f"Date fin: {event.end_date.strftime('%Y-%m-%d %H:%M')}")
        print(f"Durée: {event.duration_days} jour(s)")

        if event.support_contact:
            print(f"Support assigné: {event.support_contact.full_name}")
        else:
            print("Support assigné: Non assigné")

        print(f"Contrat ID: {event.contract_id}")
        if event.contract:
            print(f"Client: {event.contract.client.full_name}")
            print(f"Entreprise: {event.contract.client.company_name}")
            print(f"Commercial: {event.contract.commercial_contact.full_name}")

        if event.notes:
            print(f"Notes: {event.notes}")

        print(f"Créé le: {event.created_at.strftime('%Y-%m-%d %H:%M')}")
        if event.updated_at:
            print(f"Modifié le: {event.updated_at.strftime('%Y-%m-%d %H:%M')}")

    def _display_events_table(self, events: List[Event]):
        """
        Afficher un tableau formaté des événements avec Rich.

        Cette méthode utilitaire présente les événements dans un
        format tabulaire professionnel avec codes couleur et styles.

        Formatage professionnel:
            - Tableau Rich avec bordures et couleurs
            - Colonnes optimisées pour informations essentielles
            - Codes couleur selon statuts et priorités
            - Truncation intelligente des textes longs
            - Alignement et espacement optimal

        Informations affichées:
            - ID événement et nom complet
            - Client associé via contrat
            - Personnel support assigné
            - Dates de début et fin
            - Lieu et nombre de participants
            - Statuts visuels avec indicateurs
        """
        # Construction données tableau avec formatage
        header = f"{'ID':<5} {'Nom':<25} {'Client':<20} {'Date':<12} " \
                 f"{'Lieu':<20} {'Support':<15}"
        print(header)
        print("-" * len(header))

        for event in events:
            # Formatage client avec troncature intelligente
            client_name = event.contract.client.full_name[:19] if event.contract else "N/A"

            # Formatage personnel support avec statut assignation
            support_name = (event.support_contact.full_name[:14]
                            if event.support_contact else "Non assigné")

            # Formatage date avec validation existence
            date_str = event.start_date.strftime('%Y-%m-%d')

            # Affichage ligne tableau avec alignement optimal
            print(f"{event.id:<5} {event.name[:24]:<25} {client_name:<20} "
                  f"{date_str:<12} {event.location[:19]:<20} {support_name:<15}")

    def _get_available_supports(self):
        """
        Récupérer la liste des utilisateurs support disponibles.

        Cette méthode utilitaire interroge la base de données pour
        obtenir tous les utilisateurs du département SUPPORT.

        Fonctionnalité de sélection:
            - Requête filtrée par département SUPPORT
            - Liste complète personnel technique
            - Données pour interface assignation
            - Validation disponibilité et permissions

        Retour:
            - Liste des utilisateurs SUPPORT actifs
            - Données complètes pour sélection
            - Support pour interface assignation
        """
        # Requête base de données pour personnel support
        from src.models.user import User, Department
        supports = self.db.query(User).filter(User.department == Department.SUPPORT).all()
        return supports

    def _prompt_support_selection(self, current_support_id=None):
        """
        Interface interactive pour sélectionner un personnel support.

        Cette méthode fournit une interface utilisateur pour choisir
        le personnel support à assigner à un événement.

        Fonctionnalités de sélection:
            - Liste interactive des supports disponibles
            - Option désassignation (aucun support)
            - Indication du support actuellement assigné
            - Validation des choix utilisateur
            - Interface intuitive avec numérotation

        Paramètres:
            - current_support_id: ID du support actuellement assigné

        Retour:
            - ID du support sélectionné ou None pour désassignation
            - Validation des saisies et gestion erreurs

        Interface utilisateur:
            - Menu numéroté avec options claires
            - Indication visuelle assignation actuelle
            - Validation saisie et gestion erreurs
            - Retour utilisateur avec confirmations
        """
        # Vérification disponibilité personnel support
        supports = self._get_available_supports()

        if not supports:
            # Aucun personnel support disponible dans le système
            self.display_warning("Aucun utilisateur support disponible")
            return None

        # Affichage menu de sélection avec options claires
        print("\nSupport assigné :")
        print("  0 - Aucun support (non assigné)")

        # Liste numérotée avec indications visuelles
        for i, support in enumerate(supports, 1):
            current_marker = " (actuel)" if current_support_id == support.id else ""
            print(f"  {i} - {support.full_name} ({support.email}){current_marker}")

        # Boucle de validation saisie utilisateur
        while True:
            try:
                choice = self.prompt_user(f"Votre choix [0-{len(supports)}]", required=True)
                choice_int = int(choice)

                if choice_int == 0:
                    # Choix désassignation
                    return None
                elif 1 <= choice_int <= len(supports):
                    # Choix support valide
                    return supports[choice_int - 1].id
                else:
                    # Choix hors limites
                    self.display_error(f"Choix invalide. Choisissez entre 0 et {len(supports)}")
            except ValueError:
                # Saisie non numérique
                self.display_error("Veuillez saisir un nombre valide")

    def create_event_command_for_contract(self, contract_id: int):
        """
        Créer un nouvel événement pour un contrat spécifique.

        Cette méthode spécialisée crée un événement directement lié
        à un contrat existant avec validation des prérequis.

        Prérequis de création:
            - Contrat doit exister et être signé
            - Utilisateur doit avoir permissions création
            - Contrat ne doit pas avoir d'événement existant
            - Validation des données événement complètes

        Processus de création spécialisé:
            - Validation contrat signé et disponible
            - Configuration événement avec données contrat
            - Assignation initiale personnel support
            - Validation contraintes temporelles et logistiques
            - Enregistrement avec liens contrat-événement
        """
        from datetime import datetime

        try:
            # Authentification et configuration permissions
            current_user = self.auth_service.require_authentication()
            self.event_controller.set_current_user(current_user)

            # Validation et récupération du contrat cible
            from src.controllers.contract_controller import ContractController
            contract_controller = ContractController(self.db)
            contract_controller.set_current_user(current_user)

            contract = contract_controller.get_contract_by_id(contract_id)
            if not contract:
                self.display_error(f"Contrat avec l'ID {contract_id} introuvable")
                return

            # Vérification statut contrat pour création événement
            from src.models.contract import ContractStatus
            if contract.status != ContractStatus.SIGNED:
                self.display_error("Seuls les contrats signés peuvent avoir des événements")
                return

            # En-tête de création avec contexte contrat
            self.display_info(f"\n─────────── CRÉATION D'UN ÉVÉNEMENT POUR LE CONTRAT {contract.id} ───────────")

            # Affichage informations contrat pour contexte
            self.display_info(f"\nContrat : #{contract.id}")
            self.display_info(f"Client : {contract.client.full_name}")
            self.display_info(f"Entreprise : {contract.client.company_name}")
            self.display_info(f"Commercial : {contract.commercial_contact.full_name}")

            print()

            # Saisie des données de l'événement
            name = self.prompt_user("Nom de l'événement", required=True)

            # Date et heure de début
            while True:
                try:
                    start_date_str = self.prompt_user("Date de début (YYYY-MM-DD HH:MM)", required=True)
                    start_date = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M")

                    if start_date < datetime.now():
                        self.display_error("La date de début ne peut pas être dans le passé")
                        continue
                    break
                except ValueError:
                    self.display_error("Format de date invalide. Utilisez : YYYY-MM-DD HH:MM")

            # Date et heure de fin
            while True:
                try:
                    end_date_str = self.prompt_user("Date de fin (YYYY-MM-DD HH:MM)", required=True)
                    end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M")

                    if end_date <= start_date:
                        self.display_error("La date de fin doit être après la date de début")
                        continue
                    break
                except ValueError:
                    self.display_error("Format de date invalide. Utilisez : YYYY-MM-DD HH:MM")

            # Lieu
            location = self.prompt_user("Lieu de l'événement", required=True)

            # Nombre d'invités
            while True:
                try:
                    attendees_str = self.prompt_user("Nombre d'invités", required=True)
                    attendees = int(attendees_str)
                    if attendees < 0:
                        self.display_error("Le nombre d'invités doit être positif")
                        continue
                    break
                except ValueError:
                    self.display_error("Veuillez saisir un nombre valide")

            # Notes (optionnel)
            notes = self.prompt_user("Notes sur l'événement (optionnel)")
            if not notes.strip():
                notes = None

            # Sélection du support (optionnel)
            support_contact_id = self._prompt_support_selection()

            # Créer l'événement
            event = self.event_controller.create_event(
                contract_id=contract_id,
                name=name,
                start_date=start_date,
                end_date=end_date,
                location=location,
                attendees=attendees,
                notes=notes,
                support_contact_id=support_contact_id
            )

            self.display_success_box(
                "ÉVÉNEMENT CRÉÉ",
                f"Événement créé avec succès !\n\n"
                f"ID: {event.id}\n"
                f"Nom: {event.name}\n"
                f"Contrat: #{event.contract.id}\n"
                f"Client: {event.contract.client.full_name}\n"
                f"Date de début: {event.start_date.strftime('%Y-%m-%d %H:%M')}\n"
                f"Date de fin: {event.end_date.strftime('%Y-%m-%d %H:%M')}\n"
                f"Lieu: {event.location}\n"
                f"Invités: {event.attendees}\n"
                f"Support assigné: {'Non assigné' if not event.support_contact else event.support_contact.full_name}"
            )

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(VALIDATION_MESSAGES["authorization_error"].format(error=e))
        except Exception as e:
            self.display_error(f"Erreur lors de la création de l'événement: {e}")

    def update_event_command(self, event_id: int):
        """Mettre à jour un événement existant"""
        from datetime import datetime

        try:
            current_user = self.auth_service.require_authentication()
            self.event_controller.set_current_user(current_user)

            # Récupérer l'événement
            event = self.event_controller.get_event_by_id(event_id)
            if not event:
                self.display_error(f"Événement avec l'ID {event_id} introuvable")
                return

            self.display_info(f"\n────────────── MODIFICATION DE L'ÉVÉNEMENT {event.id} ──────────────")

            # Afficher les détails actuels
            self.display_info_box(
                "DÉTAILS DE L'ÉVÉNEMENT",
                f"ID: {event.id}\n"
                f"Nom: {event.name}\n"
                f"Contrat: #{event.contract.id}\n"
                f"Client: {event.contract.client.full_name}\n"
                f"Date de début: {event.start_date.strftime('%Y-%m-%d %H:%M')}\n"
                f"Date de fin: {event.end_date.strftime('%Y-%m-%d %H:%M')}\n"
                f"Lieu: {event.location}\n"
                f"Invités: {event.attendees}\n"
                f"Support: {'Non assigné' if not event.support_contact else event.support_contact.full_name}\n"
                f"Créé le: {event.created_at.strftime('%Y-%m-%d %H:%M')}"
            )

            print("\nLaissez vide pour conserver la valeur actuelle")

            # Nom de l'événement
            name = self.prompt_user(f"Nom ({event.name})")
            if not name.strip():
                name = None

            # Date de début
            start_date = None
            start_input = self.prompt_user(f"Date de début ({event.start_date.strftime('%Y-%m-%d %H:%M')})")
            if start_input.strip():
                try:
                    start_date = datetime.strptime(start_input, "%Y-%m-%d %H:%M")
                    if start_date < datetime.now():
                        self.display_error("La date de début ne peut pas être dans le passé")
                        return
                except ValueError:
                    self.display_error("Format de date invalide")
                    return

            # Date de fin
            end_date = None
            end_input = self.prompt_user(f"Date de fin ({event.end_date.strftime('%Y-%m-%d %H:%M')})")
            if end_input.strip():
                try:
                    end_date = datetime.strptime(end_input, "%Y-%m-%d %H:%M")
                    check_start = start_date if start_date is not None else event.start_date
                    if end_date <= check_start:
                        self.display_error("La date de fin doit être après la date de début")
                        return
                except ValueError:
                    self.display_error("Format de date invalide")
                    return

            # Lieu
            location = self.prompt_user(f"Lieu ({event.location})")
            if not location.strip():
                location = None

            # Nombre d'invités
            attendees = None
            attendees_input = self.prompt_user(f"Nombre d'invités ({event.attendees})")
            if attendees_input.strip():
                try:
                    attendees = int(attendees_input)
                    if attendees < 0:
                        self.display_error("Le nombre d'invités doit être positif")
                        return
                except ValueError:
                    self.display_error("Nombre invalide")
                    return

            # Notes
            notes = self.prompt_user(f"Notes ({event.notes or 'Aucune'})")
            if not notes.strip():
                notes = None

            # Support assigné
            support_contact_id = None
            change_support = self.prompt_user("Changer le support assigné ? [y/n]")
            if change_support.lower() in ['y', 'yes', 'o', 'oui']:
                current_support_id = event.support_contact_id
                support_contact_id = self._prompt_support_selection(current_support_id)

            # Mettre à jour l'événement
            update_data = {}
            if name is not None:
                update_data['name'] = name
            if start_date is not None:
                update_data['start_date'] = start_date
            if end_date is not None:
                update_data['end_date'] = end_date
            if location is not None:
                update_data['location'] = location
            if attendees is not None:
                update_data['attendees'] = attendees
            if notes is not None:
                update_data['notes'] = notes
            if support_contact_id is not None or change_support.lower() in ['y', 'yes', 'o', 'oui']:
                update_data['support_contact_id'] = support_contact_id

            updated_event = self.event_controller.update_event(
                event_id=event_id,
                **update_data
            )

            self.display_success(EVENT_MESSAGES["update_success"])

            support_display = ("Non assigné" if not updated_event.support_contact
                               else updated_event.support_contact.full_name)

            # Afficher les nouveaux détails
            self.display_info_box(
                "DÉTAILS DE L'ÉVÉNEMENT",
                f"ID: {updated_event.id}\n"
                f"Nom: {updated_event.name}\n"
                f"Contrat: #{updated_event.contract.id}\n"
                f"Client: {updated_event.contract.client.full_name}\n"
                f"Date de début: {updated_event.start_date.strftime('%Y-%m-%d %H:%M')}\n"
                f"Date de fin: {updated_event.end_date.strftime('%Y-%m-%d %H:%M')}\n"
                f"Lieu: {updated_event.location}\n"
                f"Invités: {updated_event.attendees}\n"
                f"Support: {support_display}\n"
                f"Créé le: {updated_event.created_at.strftime('%Y-%m-%d %H:%M')}"
            )

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(VALIDATION_MESSAGES["authorization_error"].format(error=e))
        except Exception as e:
            self.display_error(f"Erreur lors de la mise à jour de l'événement: {e}")

    def assign_support_command(self, event_id: int, support_id: int):
        """Assigner un support à un événement"""
        try:
            current_user = self.auth_service.require_authentication()
            self.event_controller.set_current_user(current_user)

            updated_event = self.event_controller.assign_support_to_event(event_id, support_id)

            self.display_success_box(
                "SUPPORT ASSIGNÉ",
                f"Support assigné avec succès !\n\n"
                f"Événement: {updated_event.name}\n"
                f"Support: {updated_event.support_contact.full_name}\n"
                f"Client: {updated_event.contract.client.full_name}"
            )

        except (AuthenticationError, AuthorizationError) as e:
            self.display_error(VALIDATION_MESSAGES["authorization_error"].format(error=e))
        except Exception as e:
            self.display_error(f"Erreur lors de l'assignation: {e}")
