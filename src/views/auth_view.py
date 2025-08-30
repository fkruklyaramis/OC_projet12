
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from datetime import datetime, timezone
from src.utils.auth_utils import AuthenticationError
from .base_view import BaseView


class AuthView(BaseView):
    """Vue pour l'authentification avec interface Rich"""

    def __init__(self):
        super().__init__()
        # AuthView utilise directement le service d'auth de BaseView

    def _display_welcome_logo(self):
        """Afficher le logo d'accueil Epic Events"""
        title_text = Text()
        title_text.append("Epic Events CRM", style="bold cyan")
        title_text.append(" - Système de gestion des événements", style="white")

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
        """Commande de connexion avec interface améliorée"""
        try:
            self.display_header("CONNEXION EPIC EVENTS CRM")

            if self.auth_service.is_authenticated():

                current_user = self.auth_service.get_current_user()
                if current_user:
                    self.display_warning(f"Déjà connecté en tant que: "
                                         f"{current_user.full_name} "
                                         f"({current_user.email})")

                    if not self.confirm_action("Voulez-vous vous reconnecter?"):
                        return

                    self.auth_service.logout()

            if not email:
                email = self.get_user_input("Email")

            password = self.get_user_input("Mot de passe", password=True)

            # Animation de connexion
            with self.console.status("[bold green]Connexion en cours..."):
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
                self.display_panel(welcome_content, "CONNEXION RÉUSSIE", style="green", border_style="green")
            else:
                self.display_error("Échec de la connexion")

        except AuthenticationError as e:
            self.display_error(f"Erreur d'authentification: {e}")
        except Exception as e:
            self.display_error(f"Erreur: {e}")

    def status_command(self):
        """Afficher le statut de connexion avec style"""
        try:
            self.display_header("STATUT DE CONNEXION")

            if self.auth_service.is_authenticated():
                user_data = self.auth_service.get_token_info()
                current_user = self.auth_service.get_current_user()

                if current_user and user_data:
                    # Tableau de statut
                    table = Table(title="Informations de connexion", box=box.ROUNDED, style="green")
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
                    self.display_error("Token invalide ou expiré")
            else:
                # Panneau de statut déconnecté
                disconnected_content = """
[bold red]Statut: DÉCONNECTÉ[/bold red]

[yellow]Utilisez la commande suivante pour vous connecter:[/yellow]
[cyan]python epicevents.py login[/cyan]
                """
                self.display_panel(disconnected_content, "STATUT", style="red", border_style="red")

        except Exception as e:
            self.display_error(f"Erreur: {e}")

    def logout_command(self):
        """Commande de déconnexion avec style"""
        try:
            self.display_header("DÉCONNEXION")

            if not self.auth_service.is_authenticated():
                self.display_info("Vous n'êtes pas connecté")
                return

            current_user = self.auth_service.get_current_user()

            with self.console.status("[bold red]Déconnexion en cours..."):
                success = self.auth_service.logout()

            if success:
                logout_content = f"""
[bold green]Déconnexion réussie ![/bold green]

À bientôt [cyan]{current_user.full_name}[/cyan] !
                """
                self.display_panel(logout_content, "AU REVOIR", style="yellow", border_style="yellow")
            else:
                self.display_error("Erreur lors de la déconnexion")

        except Exception as e:
            self.display_error(f"Erreur: {e}")

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
                self.display_warning("Non connecté")
        except Exception as e:
            self.display_error(f"Erreur: {e}")
