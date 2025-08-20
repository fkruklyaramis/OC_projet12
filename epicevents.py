import click
from src.database.init_db import init_database
from src.views.auth_view import AuthView
from src.views.client_view import ClientView
from src.views.contract_view import ContractView
from src.views.event_view import EventView


@click.group()
def cli():
    """Epic Events CRM - Système de gestion des événements"""
    pass


# === COMMANDES D'AUTHENTIFICATION ===
@cli.command()
@click.option('--email', help='Adresse email')
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
    """Afficher le statut de connexion"""
    auth_view = AuthView()
    auth_view.status_command()


@cli.command()
def whoami():
    """Afficher l'utilisateur actuel"""
    auth_view = AuthView()
    auth_view.whoami_command()


# === COMMANDE D'INITIALISATION ===
@cli.command()
def init():
    """Initialiser la base de données avec des données d'exemple"""
    if init_database():
        click.echo("Base de données initialisée avec succès!")
        click.echo("Vous pouvez maintenant vous connecter avec:")
        click.echo("  python epicevents.py login --email admin@epicevents.com")
    else:
        click.echo("Erreur lors de l'initialisation de la base de données")


# === COMMANDES CLIENTS ===
@cli.group()
def client():
    """Gestion des clients"""
    pass


@client.command('list')
@click.option('--mine', is_flag=True, help='Afficher seulement mes clients')
def list_clients(mine):
    """Lister les clients"""
    client_view = ClientView()
    client_view.list_clients_command(my_clients=mine)


@client.command('search')
def search_clients():
    """Rechercher des clients"""
    client_view = ClientView()
    client_view.search_clients_command()


# === COMMANDES CONTRATS ===
@cli.group()
def contract():
    """Gestion des contrats"""
    pass


@contract.command('list')
def list_contracts():
    """Lister tous les contrats"""
    contract_view = ContractView()
    contract_view.list_all_contracts_command()


@contract.command('mine')
def my_contracts():
    """Lister mes contrats (commerciaux)"""
    contract_view = ContractView()
    contract_view.list_my_contracts_command()


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
    """Voir les détails d'un contrat"""
    contract_view = ContractView()
    contract_view.view_contract_command(contract_id)


@contract.command('search')
def search_contracts():
    """Rechercher des contrats"""
    contract_view = ContractView()
    contract_view.search_contracts_command()


# === COMMANDES EVENEMENTS ===
@cli.group()
def event():
    """Gestion des événements"""
    pass


@event.command('list')
def list_events():
    """Lister tous les événements"""
    event_view = EventView()
    event_view.list_all_events_command()


@event.command('mine')
def my_events():
    """Lister mes événements (support/commercial)"""
    event_view = EventView()
    event_view.list_my_events_command()


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
    """Voir les détails d'un événement"""
    event_view = EventView()
    event_view.view_event_command(event_id)


@event.command('search')
def search_events():
    """Rechercher des événements"""
    event_view = EventView()
    event_view.search_events_command()


if __name__ == '__main__':
    cli()
