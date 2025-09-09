
"""
Vue d'authentification pour Epic Events CRM

Ce module fournit l'interface utilisateur pour toutes les opérations
d'authentification : connexion, déconnexion, affichage du statut utilisateur
et gestion des sessions avec une présentation visuelle attractive.

Fonctionnalités d'authentification:
    - Interface de connexion avec logo Epic Events
    - Gestion des sessions persistantes via JWT
    - Affichage du statut d'authentification
    - Déconnexion sécurisée avec nettoyage
    - Messages d'erreur contextuels et guidage utilisateur

Interface utilisateur:
    - Logo ASCII Epic Events pour branding
    - Messages colorés selon le contexte (succès, erreur, warning)
    - Prompts sécurisés pour mots de passe (masqués)
    - Confirmation visuelle des actions d'authentification
    - Navigation intuitive avec feedback immédiat

Sécurité:
    - Masquage automatique des mots de passe
    - Validation des sessions avant actions
    - Nettoyage sécurisé lors de la déconnexion
    - Messages d'erreur sans fuite d'information
    - Protection contre tentatives multiples

Gestion des sessions:
    - Détection automatique de sessions existantes
    - Affichage des informations utilisateur connecté
    - Gestion gracieuse des tokens expirés
    - Persistance entre redémarrages d'application

Fichier: src/views/auth_view.py
"""

from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from datetime import datetime, timezone
from src.utils.auth_utils import AuthenticationError
from src.config.messages import PROMPTS, AUTH_MESSAGES, CONFIRMATIONS
from .base_view import BaseView


class AuthView(BaseView):
    """
    Vue spécialisée pour les opérations d'authentification et de session.

    Cette classe hérite de BaseView et ajoute les fonctionnalités spécifiques
    à l'authentification avec une présentation visuelle cohérente et sécurisée.

    Responsabilités:
        - Interface de connexion/déconnexion utilisateur
        - Affichage du logo et branding Epic Events
        - Gestion des messages d'authentification
        - Validation des sessions et gestion des erreurs
        - Feedback utilisateur pour opérations d'auth

    Interface visuelle:
        - Logo ASCII artistique pour identité visuelle
        - Panels stylés pour encadrer les sections importantes
        - Messages colorés selon gravité et contexte
        - Tables pour affichage d'informations utilisateur

    Sécurité:
        - Validation systématique des entrées utilisateur
        - Masquage des mots de passe dans l'interface
        - Gestion sécurisée des erreurs d'authentification
        - Nettoyage automatique des sessions expirées
    """

    def __init__(self):
        """
        Initialiser la vue d'authentification.

        Hérite de BaseView pour accès aux services partagés
        (base de données, console Rich, service d'authentification).
        """
        super().__init__()
        # AuthView utilise directement le service d'auth de BaseView

    def _display_welcome_logo(self):
        """
        Afficher le logo d'accueil Epic Events avec branding complet.

        Cette méthode présente l'identité visuelle de l'application avec
        un logo ASCII artistique et les textes de titre/sous-titre.

        Éléments visuels:
            - Logo ASCII Epic Events en art textuel
            - Titre principal avec style cyan gras
            - Sous-titre descriptif en blanc
            - Panel encadré avec bordure double
            - Style général cyan pour cohérence de marque
        """
        title_text = Text()
        title_text.append(AUTH_MESSAGES["app_title"], style="bold cyan")
        title_text.append(AUTH_MESSAGES["app_subtitle"], style="white")

        # Logo ASCII artistique Epic Events
        logo = """
    ███████╗██████╗ ██╗ ██████╗    ███████╗██╗   ██╗███████╗███╗   ██╗████████╗███████╗
    ██╔════╝██╔══██╗██║██╔════╝    ██╔════╝██║   ██║██╔════╝████╗  ██║╚══██╔══╝██╔════╝
    █████╗  ██████╔╝██║██║         █████╗  ██║   ██║█████╗  ██╔██╗ ██║   ██║   ███████╗
    ██╔══╝  ██╔═══╝ ██║██║         ██╔══╝  ╚██╗ ██╔╝██╔══╝  ██║╚██╗██║   ██║   ╚════██║
    ███████╗██║     ██║╚██████╗    ███████╗ ╚████╔╝ ███████╗██║ ╚████║   ██║   ███████║
    ╚══════╝╚═╝     ╚═╝ ╚═════╝    ╚══════╝  ╚═══╝  ╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝
        """

        self.console.print(Panel(
            logo,
            title=title_text,
            box=box.DOUBLE,
            style="cyan"
        ))

    def login_command(self, email: str = None):
        """
        Interface de connexion utilisateur avec gestion complète des cas.

        Cette méthode gère le processus complet de connexion avec validation,
        feedback utilisateur et gestion des sessions existantes.

        Args:
            email: Email pré-rempli (optionnel, pour réutilisation)

        Fonctionnalités:
            - Vérification de session existante
            - Saisie sécurisée email/mot de passe
            - Validation et authentification
            - Gestion des erreurs avec messages contextuels
            - Confirmation visuelle de connexion réussie

        Sécurité:
            - Masquage automatique du mot de passe
            - Validation des entrées utilisateur
            - Gestion des tentatives d'authentification échouées
            - Protection contre bruteforce via feedback
        """
        try:
            self.display_header(AUTH_MESSAGES["login_header"])

            # Vérification session existante
            if self.auth_service.is_authenticated():

                current_user = self.auth_service.get_current_user()
                if current_user:
                    self.display_warning(AUTH_MESSAGES["already_connected"].format(
                        user_name=current_user.full_name,
                        user_email=current_user.email
                    ))

                    if not self.confirm_action(CONFIRMATIONS["reconnect"]):
                        return

                    self.auth_service.logout()

            if not email:
                email = self.get_user_input(PROMPTS["email"])

            password = self.get_user_input(PROMPTS["password"], password=True)

            # Animation de connexion
            with self.console.status(AUTH_MESSAGES["connecting_status"]):
                user = self.auth_service.login(email, password)

            if user:
                # Afficher le logo d'accueil
                self._display_welcome_logo()
                # Panneau de bienvenue stylé
                welcome_content = f"""
[bold green]Bienvenue {user.full_name} ![/bold green]

[cyan]Département:[/cyan] {user.department.value.upper()}
[cyan]Numéro employé:[/cyan] {user.employee_number}
[cyan]Email:[/cyan] {user.email}
                """
                self.display_panel(
                    welcome_content, AUTH_MESSAGES["login_success_title"],
                    style="green", border_style="green"
                )
            else:
                self.display_error(AUTH_MESSAGES["login_failed"])

        except AuthenticationError as e:
            self.display_error(AUTH_MESSAGES["authentication_error"].format(error=e))
        except Exception as e:
            self.display_error(AUTH_MESSAGES["general_error"].format(error=e))

    def status_command(self):
        """Afficher le statut de connexion avec style"""
        try:
            self.display_header(AUTH_MESSAGES["status_header"])

            if self.auth_service.is_authenticated():
                user_data = self.auth_service.get_token_info()
                current_user = self.auth_service.get_current_user()

                if current_user and user_data:
                    # Tableau de statut
                    table = Table(title=AUTH_MESSAGES["connection_info_title"], box=box.ROUNDED, style="green")
                    table.add_column("Propriété", style="cyan", width=20)
                    table.add_column("Valeur", style="white")

                    table.add_row("Statut", "[bold green]CONNECTÉ[/bold green]")
                    table.add_row("Utilisateur", current_user.full_name)
                    table.add_row("Email", current_user.email)
                    table.add_row("Département", current_user.department.value.upper())
                    table.add_row("Numéro employé", current_user.employee_number)

                    exp_timestamp = user_data.get('exp')
                    if exp_timestamp:
                        exp_date = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
                        remaining = exp_date - datetime.now(timezone.utc)
                        if remaining.total_seconds() > 0:
                            hours = int(remaining.total_seconds() // 3600)
                            minutes = int((remaining.total_seconds() % 3600) // 60)
                            table.add_row("Token expire dans", f"{hours}h {minutes}m")
                        else:
                            table.add_row("Token", "[bold red]EXPIRÉ[/bold red]")

                    self.console.print(table)
                else:
                    self.display_error(AUTH_MESSAGES["invalid_token"])
            else:
                # Panneau de statut déconnecté
                disconnected_content = """
[bold red]Statut: DÉCONNECTÉ[/bold red]

[yellow]Utilisez la commande suivante pour vous connecter:[/yellow]
[cyan]python epicevents.py login[/cyan]
                """
                self.display_panel(
                    disconnected_content, AUTH_MESSAGES["status_title"],
                    style="red", border_style="red"
                )

        except Exception as e:
            self.display_error(AUTH_MESSAGES["general_error"].format(error=e))

    def logout_command(self):
        """Commande de déconnexion avec style"""
        try:
            self.display_header(AUTH_MESSAGES["logout_header"])

            if not self.auth_service.is_authenticated():
                self.display_info(AUTH_MESSAGES["not_connected"])
                return

            current_user = self.auth_service.get_current_user()

            with self.console.status(AUTH_MESSAGES["logout_status"]):
                success = self.auth_service.logout()

            if success:
                logout_content = f"""
[bold green]Déconnexion réussie ![/bold green]

À bientôt [cyan]{current_user.full_name}[/cyan] !
                """
                self.display_panel(
                    logout_content, AUTH_MESSAGES["goodbye_title"],
                    style="yellow", border_style="yellow"
                )
            else:
                self.display_error(AUTH_MESSAGES["logout_failed"])

        except Exception as e:
            self.display_error(AUTH_MESSAGES["general_error"].format(error=e))

    def whoami_command(self):
        """Afficher l'utilisateur actuel avec style"""
        try:
            current_user = self.auth_service.get_current_user()
            if current_user:
                user_text = Text()
                user_text.append(f"{current_user.full_name}", style="bold cyan")
                user_text.append(f" ({current_user.email})", style="dim white")
                self.console.print(user_text)
            else:
                self.display_warning(AUTH_MESSAGES["not_connected"])
        except Exception as e:
            self.display_error(AUTH_MESSAGES["general_error"].format(error=e))
