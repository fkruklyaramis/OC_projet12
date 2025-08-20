from typing import Dict, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn


class BaseView:
    """Vue de base avec Rich pour une interface CLI attractive"""

    def __init__(self):
        self.console = Console()

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

        return Prompt.ask("Votre choix", choices=list(choices.keys()))

    def confirm_action(self, message: str) -> bool:
        """Demander confirmation avec style"""
        return Confirm.ask(f"[bold yellow]{message}[/bold yellow]")

    def show_progress(self, tasks: list, description: str = "Traitement"):
        """Afficher une barre de progression"""
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
