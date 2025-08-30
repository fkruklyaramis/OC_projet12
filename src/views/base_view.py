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
    """Vue de base avec Rich pour une interface CLI attractive"""

    def __init__(self):
        self.console = Console()
        # Initialisation commune de la base de données
        SessionLocal = sessionmaker(bind=engine)
        self.db = SessionLocal()
        self.auth_service = AuthenticationService(self.db)

    def __del__(self):
        """Fermer la connexion à la base de données"""
        if hasattr(self, 'db'):
            self.db.close()

    def setup_controller(self, controller_class):
        """Configurer un contrôleur avec l'utilisateur actuel"""
        controller = controller_class(self.db)
        current_user = self.auth_service.get_current_user()
        if current_user:
            controller.set_current_user(current_user)
        return controller

    def display_success(self, message: str):
        """Afficher un message de succès"""
        self.console.print(f"[bold green]✓ {message}[/bold green]")

    def display_error(self, message: str):
        """Afficher un message d'erreur"""
        self.console.print(f"[bold red]✗ {message}[/bold red]")

    def display_warning(self, message: str):
        """Afficher un message d'avertissement"""
        self.console.print(f"[bold yellow]⚠ {message}[/bold yellow]")

    def display_info(self, message: str):
        """Afficher un message d'information"""
        self.console.print(f"[bold blue]ℹ {message}[/bold blue]")

    def display_panel(self, content: str, title: str,
                      style: str = "cyan", border_style: str = "blue"):
        """Afficher un panneau stylé"""
        panel = Panel(content, title=title, style=style,
                      border_style=border_style, box=box.ROUNDED)
        self.console.print(panel)

    def display_table(self, title: str, columns: list, data: list,
                      style: str = "cyan"):
        """Afficher un tableau stylé"""
        table = Table(title=title, style=style, box=box.ROUNDED)

        for column in columns:
            table.add_column(column['name'], style=column.get('style', 'white'),
                             justify=column.get('justify', 'left'))

        for row in data:
            table.add_row(*[str(cell) for cell in row])

        self.console.print(table)

    def get_user_input(self, prompt_text: str,
                       password: bool = False) -> Optional[str]:
        """Obtenir une saisie utilisateur avec style"""
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
        """Demander confirmation avec style"""
        return Confirm.ask(f"[bold yellow]{message}[/bold yellow]")

    def show_progress(self, tasks: list, description: str = None):
        """Afficher une barre de progression"""
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
        """Afficher un en-tête stylé"""
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
