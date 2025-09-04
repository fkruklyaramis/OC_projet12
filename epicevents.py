import rich_click as click
from rich.console import Console
from src.database.init_db import init_database
from src.views.auth_view import AuthView
from src.views.client_view import ClientView
from src.views.contract_view import ContractView
from src.views.event_view import EventView
from src.views.user_view import UserView
from src.services.logging_service import SentryLogger
from src.utils.exception_handler import ExceptionHandler
from dotenv import load_dotenv
import atexit

# Configuration Rich-Click
click.rich_click.USE_RICH_MARKUP = True
click.rich_click.USE_MARKDOWN = True
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = True
click.rich_click.STYLE_ERRORS_SUGGESTION = "magenta italic"
click.rich_click.ERRORS_SUGGESTION = (
    "Essayez 'python epicevents.py --help' pour plus d'informations."
)

console = Console()


@click.group()
def cli():
    """Epic Events CRM - Système de gestion des événements

    Application de gestion de la relation client pour Epic Events.
    Gérez vos clients, contrats et événements en toute simplicité.
    """
    # Charger les variables d'environnement au démarrage
    load_dotenv()

    # Configurer le gestionnaire global d'exceptions
    ExceptionHandler.setup_global_exception_handler()

    # Configurer la fermeture propre de Sentry à la fin du programme
    atexit.register(lambda: SentryLogger().shutdown())


# === COMMANDES D'AUTHENTIFICATION ===
@cli.command()
@click.option('--email', help='Adresse email de connexion')
def login(email):
    """Se connecter à Epic Events CRM"""
    auth_view = AuthView()
    auth_view.login_command(email)


@cli.command()
def logout():
    """Se déconnecter d'Epic Events CRM"""
    auth_view = AuthView()
    auth_view.logout_command()


@cli.command()
def status():
    """Afficher le statut de connexion actuel"""
    auth_view = AuthView()
    auth_view.status_command()


@cli.command()
def whoami():
    """Afficher l'utilisateur actuellement connecté"""
    auth_view = AuthView()
    auth_view.whoami_command()


# === COMMANDE D'INITIALISATION ===
@cli.command()
def init():
    """Initialiser la base de données avec des données d'exemple"""
    console.print("\n[bold yellow]Initialisation de la base de données...[/bold yellow]")

    with console.status("[bold green]Création des tables et données..."):
        success = init_database()

    if success:
        from rich.panel import Panel
        from rich import box
        success_content = """
[bold green]Base de données initialisée avec succès ![/bold green]

[cyan]Comptes disponibles:[/cyan]
• [yellow]admin@epicevents.com[/yellow] (mot de passe: Admin123!) - GESTION
• [yellow]marie.martin@epicevents.com[/yellow] (mot de passe: Commercial123!) - COMMERCIAL
• [yellow]sophie.bernard@epicevents.com[/yellow] (mot de passe: Support123!) - SUPPORT

[cyan]Commande de connexion:[/cyan]
[dim]python epicevents.py login --email admin@epicevents.com[/dim]
        """
        console.print(Panel(success_content, title="INITIALISATION RÉUSSIE",
                            style="green", box=box.ROUNDED))
    else:
        console.print("[bold red]Erreur lors de l'initialisation de la base de données[/bold red]")


# === GROUPE UTILISATEURS ===
@cli.group()
def user():
    """Gestion des collaborateurs (gestion uniquement)"""
    pass


@user.command('list')
@click.option('--department', type=click.Choice(['commercial', 'support', 'gestion']),
              help='Filtrer par département')
def list_users(department):
    """Lister les utilisateurs"""
    user_view = UserView()
    user_view.list_users_command(department)


@user.command('create')
def create_user():
    """Créer un nouveau collaborateur"""
    user_view = UserView()
    user_view.create_user_command()


@user.command('update')
@click.argument('user_id', type=int)
def update_user(user_id):
    """Modifier un collaborateur"""
    user_view = UserView()
    user_view.update_user_command(user_id)


@user.command('delete')
@click.argument('user_id', type=int)
def delete_user(user_id):
    """Supprimer un collaborateur"""
    user_view = UserView()
    user_view.delete_user_command(user_id)


@user.command('password')
@click.argument('user_id', type=int, required=False)
def change_password(user_id):
    """Changer le mot de passe (son propre mot de passe ou celui d'un autre si gestion)"""
    user_view = UserView()
    user_view.change_password_command(user_id)


@user.command('search')
def search_users():
    """Rechercher des collaborateurs"""
    user_view = UserView()
    user_view.search_users_command()


# === GROUPE CLIENTS ===
@cli.group()
def client():
    """Gestion des clients et prospects"""
    pass


@client.command('list')
@click.option('--mine', is_flag=True, help='Afficher seulement mes clients')
def list_clients(mine):
    """Lister les clients"""
    client_view = ClientView()
    client_view.list_clients_command(my_clients=mine)


@client.command('create')
@click.option('--commercial-id', type=int, help='ID du commercial responsable')
def create_client(commercial_id):
    """Créer un nouveau client"""
    client_view = ClientView()
    client_view.create_client_command(commercial_id)


@client.command('update')
@click.argument('client_id', type=int)
def update_client(client_id):
    """Modifier un client"""
    client_view = ClientView()
    client_view.update_client_command(client_id)


@client.command('delete')
@click.argument('client_id', type=int)
def delete_client(client_id):
    """Supprimer un client"""
    client_view = ClientView()
    client_view.delete_client_command(client_id)


@client.command('assign')
@click.argument('client_id', type=int)
@click.argument('commercial_id', type=int)
def assign_client(client_id, commercial_id):
    """Assigner un client à un commercial (gestion uniquement)"""
    client_view = ClientView()
    client_view.assign_client_command(client_id, commercial_id)


@client.command('search')
def search_clients():
    """Rechercher des clients par critères"""
    client_view = ClientView()
    client_view.search_clients_command()


# === GROUPE CONTRATS ===
@cli.group()
def contract():
    """Gestion des contrats et devis"""
    pass


@contract.command('list')
def list_contracts():
    """Lister tous les contrats (gestion uniquement)"""
    contract_view = ContractView()
    contract_view.list_all_contracts_command()


@contract.command('mine')
def my_contracts():
    """Lister mes contrats (commerciaux)"""
    contract_view = ContractView()
    contract_view.list_my_contracts_command()


@contract.command('create')
@click.argument('client_id', type=int)
def create_contract(client_id):
    """Créer un nouveau contrat pour un client"""
    contract_view = ContractView()
    contract_view.create_contract_command(client_id)


@contract.command('update')
@click.argument('contract_id', type=int)
def update_contract(contract_id):
    """Modifier un contrat"""
    contract_view = ContractView()
    contract_view.update_contract_command(contract_id)


@contract.command('sign')
@click.argument('contract_id', type=int)
def sign_contract(contract_id):
    """Signer un contrat"""
    contract_view = ContractView()
    contract_view.sign_contract_command(contract_id)


@contract.command('unsigned')
def unsigned_contracts():
    """Lister les contrats non signés"""
    contract_view = ContractView()
    contract_view.list_unsigned_contracts_command()


@contract.command('unpaid')
def unpaid_contracts():
    """Lister les contrats avec montants dus"""
    contract_view = ContractView()
    contract_view.list_unpaid_contracts_command()


@contract.command('view')
@click.argument('contract_id', type=int)
def view_contract(contract_id):
    """Voir les détails d'un contrat spécifique"""
    contract_view = ContractView()
    contract_view.view_contract_command(contract_id)


@contract.command('search')
def search_contracts():
    """Rechercher des contrats par critères"""
    contract_view = ContractView()
    contract_view.search_contracts_command()


# === GROUPE EVENEMENTS ===
@cli.group()
def event():
    """Gestion des événements et manifestations"""
    pass


@event.command('list')
def list_events():
    """Lister tous les événements (gestion uniquement)"""
    event_view = EventView()
    event_view.list_all_events_command()


@event.command('mine')
def my_events():
    """Lister mes événements (support/commercial)"""
    event_view = EventView()
    event_view.list_my_events_command()


@event.command('create')
@click.argument('contract_id', type=int)
def create_event(contract_id):
    """Créer un nouvel événement pour un contrat signé"""
    event_view = EventView()
    event_view.create_event_command(contract_id)


@event.command('update')
@click.argument('event_id', type=int)
def update_event(event_id):
    """Modifier un événement"""
    event_view = EventView()
    event_view.update_event_command(event_id)


@event.command('assign')
@click.argument('event_id', type=int)
@click.argument('support_id', type=int)
def assign_event(event_id, support_id):
    """Assigner un support à un événement (gestion uniquement)"""
    event_view = EventView()
    event_view.assign_support_command(event_id, support_id)


@event.command('upcoming')
@click.option('--days', default=30, help='Nombre de jours à venir (défaut: 30)')
def upcoming_events(days):
    """Lister les événements à venir"""
    event_view = EventView()
    event_view.list_upcoming_events_command(days)


@event.command('unassigned')
def unassigned_events():
    """Lister les événements sans support assigné"""
    event_view = EventView()
    event_view.list_unassigned_events_command()


@event.command('view')
@click.argument('event_id', type=int)
def view_event(event_id):
    """Voir les détails d'un événement spécifique"""
    event_view = EventView()
    event_view.view_event_command(event_id)


@event.command('search')
def search_events():
    """Rechercher des événements par critères"""
    event_view = EventView()
    event_view.search_events_command()


if __name__ == '__main__':
    cli()
