"""
Vue de base pour l'interface CLI Epic Events CRM

Ce module fournit la classe BaseView qui sert de fondation pour toutes les vues
de l'application, implémentant une interface CLI moderne et attractive avec
Rich, gestion centralisée de la base de données et patterns de présentation uniformes.

Architecture de présentation:
    1. Interface unifiée: Classe de base pour toutes les vues métier
    2. Rich Integration: Interface CLI moderne avec couleurs et formatage
    3. Gestion centralisée: Base de données et authentification partagées
    4. Patterns uniformes: Messages, saisies et affichages standardisés

Fonctionnalités principales:
    - Gestion automatique des sessions de base de données
    - Interface Rich avec console, tables, panels et prompts
    - Messages colorés et formatés (succès, erreur, warning, info)
    - Saisie utilisateur sécurisée avec validation
    - Headers et séparateurs pour navigation claire
    - Intégration authentification avec contrôleurs

Composants Rich utilisés:
    - Console: Affichage principal avec support couleurs
    - Table: Présentation tabulaire des données
    - Panel: Encadrement des sections importantes
    - Text: Formatage avancé du texte
    - Prompt: Saisie utilisateur interactive
    - Progress: Barres de progression pour opérations longues

Gestion des ressources:
    - Sessions SQLAlchemy: Création et fermeture automatique
    - Connexions base: Pool de connexions via engine partagé
    - Mémoire: Nettoyage automatique via __del__
    - Contrôleurs: Configuration centralisée avec utilisateur courant

Patterns d'affichage:
    - Messages typés: Succès (vert), erreur (rouge), warning (jaune), info (bleu)
    - Headers formatés: Titres de sections avec encadrement
    - Tableaux uniformes: Colonnes alignées et styles cohérents
    - Confirmation utilisateur: Prompts sécurisés avec validation

Sécurité et robustesse:
    - Validation des entrées utilisateur
    - Gestion gracieuse des erreurs d'affichage
    - Protection contre injection via Rich
    - Nettoyage automatique des ressources

Fichier: src/views/base_view.py
"""

from typing import Dict, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn
from sqlalchemy.orm import sessionmaker
from src.database.connection import engine
from src.services.auth_service import AuthenticationService
from src.config.messages import VALIDATION_MESSAGES, PROMPTS, GENERAL_MESSAGES


class BaseView:
    """
    Classe de base pour toutes les vues CLI de l'application Epic Events.

    Cette classe fournit l'infrastructure commune pour l'affichage, la saisie
    utilisateur et la gestion des ressources, garantissant une expérience
    utilisateur cohérente dans toute l'application.

    Responsabilités:
        - Initialisation et gestion des sessions de base de données
        - Configuration du service d'authentification
        - Méthodes d'affichage standardisées avec Rich
        - Saisie utilisateur sécurisée et validée
        - Interface commune pour tous les contrôleurs
        - Nettoyage automatique des ressources

    Architecture Rich:
        - Console principal pour tous les affichages
        - Styles uniformes pour messages de feedback
        - Formatage automatique des tableaux et panels
        - Gestion des couleurs et de l'accessibilité

    Gestion des ressources:
        - Session SQLAlchemy partagée avec auto-commit
        - Service d'authentification centralisé
        - Nettoyage automatique en fin de vie d'objet
        - Protection contre les fuites mémoire

    Attributs:
        console: Instance Rich Console pour affichage
        db: Session SQLAlchemy pour accès base de données
        auth_service: Service d'authentification centralisé
    """

    def __init__(self):
        """
        Initialiser la vue de base avec ressources partagées.

        Configure la console Rich, la session de base de données et
        le service d'authentification pour utilisation par les vues dérivées.
        """
        self.console = Console()
        # Initialisation session base de données avec engine partagé
        SessionLocal = sessionmaker(bind=engine)
        self.db = SessionLocal()
        self.auth_service = AuthenticationService(self.db)

    def __del__(self):
        """
        Nettoyer les ressources lors de la destruction de l'objet.

        Ferme proprement la session de base de données pour éviter
        les fuites de connexions et garantir la cohérence transactionnelle.
        """
        if hasattr(self, 'db'):
            self.db.close()

    def setup_controller(self, controller_class):
        """
        Configurer un contrôleur avec l'utilisateur actuel et la session DB.

        Cette méthode standardise l'initialisation des contrôleurs en leur
        fournissant automatiquement la session de base de données et
        l'utilisateur authentifié.

        Args:
            controller_class: Classe du contrôleur à instancier

        Returns:
            Instance du contrôleur configurée et prête à utiliser

        Configuration automatique:
            - Session de base de données partagée
            - Utilisateur courant si authentifié
            - Context d'authentification valide
            - Permissions utilisateur appliquées
        """
        controller = controller_class(self.db)
        current_user = self.auth_service.get_current_user()
        if current_user:
            controller.set_current_user(current_user)
        return controller

    def display_success(self, message: str):
        """
        Afficher un message de succès avec formatage vert et icône check.

        Args:
            message: Message de succès à afficher

        Style:
            - Couleur: Vert (green)
            - Style: Gras (bold)
            - Icône: ✓ (checkmark)
            - Utilisation: Confirmations d'actions réussies
        """
        self.console.print(f"[bold green]✓ {message}[/bold green]")

    def display_error(self, message: str):
        """
        Afficher un message d'erreur avec formatage rouge et icône croix.

        Args:
            message: Message d'erreur à afficher

        Style:
            - Couleur: Rouge (red)
            - Style: Gras (bold)
            - Icône: ✗ (cross)
            - Utilisation: Erreurs, échecs d'opérations
        """
        self.console.print(f"[bold red]✗ {message}[/bold red]")

    def display_warning(self, message: str):
        """
        Afficher un message d'avertissement avec formatage jaune et icône warning.

        Args:
            message: Message d'avertissement à afficher

        Style:
            - Couleur: Jaune (yellow)
            - Style: Gras (bold)
            - Icône: ⚠ (warning)
            - Utilisation: Avertissements, actions à confirmer
        """
        self.console.print(f"[bold yellow]⚠ {message}[/bold yellow]")

    def display_info(self, message: str):
        """
        Afficher un message d'information avec formatage bleu et icône info.

        Args:
            message: Message d'information à afficher

        Style:
            - Couleur: Bleu (blue)
            - Style: Gras (bold)
            - Icône: ℹ (information)
            - Utilisation: Informations générales, guidance utilisateur
        """
        self.console.print(f"[bold blue]ℹ {message}[/bold blue]")

    def display_panel(self, content: str, title: str,
                      style: str = "cyan", border_style: str = "blue"):
        """
        Afficher un panneau stylé avec contenu encadré.

        Args:
            content: Contenu textuel à afficher dans le panneau
            title: Titre du panneau
            style: Style de couleur du panneau (défaut: cyan)
            border_style: Style de couleur de la bordure (défaut: blue)

        Utilisation:
            - Sections importantes de l'interface
            - Affichage de résultats détaillés
            - Encadrement de contenus structurés
            - Mise en valeur d'informations critiques
        """
        panel = Panel(content, title=title, style=style,
                      border_style=border_style, box=box.ROUNDED)
        self.console.print(panel)

    def display_table(self, title: str, columns: list, data: list,
                      style: str = "cyan"):
        """
        Afficher un tableau stylé avec données structurées.

        Args:
            title: Titre du tableau
            columns: Liste des définitions de colonnes avec propriétés
            data: Données à afficher (liste de listes)
            style: Style de couleur du tableau (défaut: cyan)

        Format des colonnes:
            - name: Nom de la colonne (obligatoire)
            - style: Style de couleur (optionnel, défaut: white)
            - justify: Alignement du texte (optionnel, défaut: left)

        Utilisation:
            - Affichage de listes d'entités (clients, contrats, événements)
            - Présentation de données tabulaires
            - Rapports et statistiques
            - Navigation dans les résultats de recherche
        """
        table = Table(title=title, style=style, box=box.ROUNDED)

        # Configuration dynamique des colonnes
        for column in columns:
            table.add_column(column['name'], style=column.get('style', 'white'),
                             justify=column.get('justify', 'left'))

        # Ajout des données avec conversion automatique en string
        for row in data:
            table.add_row(*[str(cell) for cell in row])

        self.console.print(table)

    def get_user_input(self, prompt_text: str,
                       password: bool = False) -> Optional[str]:
        """
        Obtenir une saisie utilisateur sécurisée avec style Rich.

        Args:
            prompt_text: Texte du prompt à afficher
            password: Si True, masque la saisie (pour mots de passe)

        Returns:
            Chaîne saisie par l'utilisateur ou None si annulé

        Sécurité:
            - Masquage automatique pour les mots de passe
            - Validation des caractères d'entrée
            - Gestion des interruptions clavier
            - Protection contre débordements de buffer

        Style:
            - Couleur: Cyan pour uniformité
            - Style: Gras pour visibilité
            - Formatage: Cohérent avec le reste de l'interface
        """
        if password:
            return Prompt.ask(f"[bold cyan]{prompt_text}[/bold cyan]",
                              password=True)
        else:
            return Prompt.ask(f"[bold cyan]{prompt_text}[/bold cyan]")

    def get_user_choice(self, choices: Dict[str, str],
                        prompt_text: str) -> str:
        """Afficher un menu de choix stylé"""
        self.console.print(f"\n[bold cyan]{prompt_text}:[/bold cyan]")

        for key, value in choices.items():
            self.console.print(f"  [yellow]{key}[/yellow] - {value}")

        return Prompt.ask(PROMPTS["user_choice"], choices=list(choices.keys()))

    def confirm_action(self, message: str) -> bool:
        """
        Demander confirmation utilisateur avec style Rich.

        Args:
            message: Message de confirmation à afficher

        Returns:
            bool: True si utilisateur confirme, False sinon

        Style:
            - Couleur: Jaune pour attirer l'attention
            - Style: Gras pour importance
            - Format: Question oui/non standard

        Utilisation:
            - Actions destructives (suppressions)
            - Modifications importantes
            - Confirmations de sécurité
            - Validation avant opérations critiques
        """
        return Confirm.ask(f"[bold yellow]{message}[/bold yellow]")

    def show_progress(self, tasks: list, description: str = None):
        """
        Afficher une barre de progression pour opérations longues.

        Args:
            tasks: Liste des tâches à traiter
            description: Description de l'opération (optionnel)

        Yields:
            Items de la liste tasks un par un avec progression

        Interface:
            - Spinner animé pour feedback visuel
            - Description textuelle de l'opération
            - Progression basée sur le nombre de tâches
            - Intégration avec console Rich principale

        Utilisation:
            - Chargement de données importantes
            - Opérations de synchronisation
            - Traitement par lots
            - Imports/exports de données
        """
        if description is None:
            description = GENERAL_MESSAGES["processing_default"]
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task(description, total=len(tasks))
            for item in tasks:
                yield item
                progress.advance(task)

    def display_header(self, title: str):
        """
        Afficher un en-tête stylé pour délimiter les sections.

        Args:
            title: Titre de la section

        Style:
            - Couleur: Magenta pour distinction
            - Style: Gras avec règle horizontale
            - Espacement: Lignes vides avant/après

        Utilisation:
            - Débuts de commandes importantes
            - Séparation des sections d'interface
            - Navigation visuelle dans l'application
            - Hiérarchisation de l'information
        """
        header_text = Text(title, style="bold magenta")
        header_text.stylize("bold")

        self.console.print()
        self.console.rule(header_text, style="magenta")
        self.console.print()

    def display_separator(self):
        """Afficher un séparateur"""
        self.console.rule(style="dim white")

    def prompt_user(self, prompt_text: str, required: bool = False,
                    password: bool = False) -> str:
        """Demander une saisie à l'utilisateur"""
        while True:
            if password:
                value = Prompt.ask(f"[bold cyan]{prompt_text}[/bold cyan]",
                                   password=True)
            else:
                value = Prompt.ask(f"[bold cyan]{prompt_text}[/bold cyan]")

            if required and not value.strip():
                self.display_error(VALIDATION_MESSAGES["information_required"])
                continue

            return value if value else ""

    def display_success_box(self, title: str, content: str):
        """Afficher une boîte de succès"""
        panel = Panel(
            content,
            title=f"[bold green]{title}[/bold green]",
            style="green",
            border_style="green",
            box=box.ROUNDED
        )
        self.console.print(panel)

    def display_info_box(self, title: str, content: str):
        """Afficher une boîte d'information"""
        panel = Panel(
            content,
            title=f"[bold blue]{title}[/bold blue]",
            style="blue",
            border_style="blue",
            box=box.ROUNDED
        )
        self.console.print(panel)
