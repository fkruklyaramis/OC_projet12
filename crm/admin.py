from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from .models import Client, Contract, Event
from .jwt_auth import JWTAuthService
from .data_service import DataService

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Administration des utilisateurs Epic Events avec informations de session"""

    list_display = ('username', 'employee_number', 'first_name', 'last_name',
                    'email', 'role', 'is_active', 'session_status', 'data_access',
                    'cli_access', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'employee_number', 'first_name', 'last_name')
    ordering = ('employee_number',)

    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Informations personnelles', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Informations Epic Events', {
            'fields': ('employee_number', 'role'),
            'description': 'Numero d\'employe unique et affiliation au departement'
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Authentification JWT', {
            'fields': ('jwt_session_info',),
            'classes': ('collapse',),
            'description': 'Informations sur les sessions JWT actives'
        }),
        ('Acces aux donnees', {
            'fields': ('data_access_info',),
            'classes': ('collapse',),
            'description': 'Statistiques d\'acces aux donnees'
        }),
        ('Interface CLI', {
            'fields': ('cli_access_info',),
            'classes': ('collapse',),
            'description': 'Informations sur l\'acces via l\'interface en ligne de commande'
        }),
        ('Dates importantes', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
        ('Informations personnelles obligatoires', {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'email'),
            'description': 'Tous ces champs sont obligatoires'
        }),
        ('Informations Epic Events', {
            'classes': ('wide',),
            'fields': ('employee_number', 'role'),
            'description': 'Numero d\'employe unique et departement'
        }),
    )

    readonly_fields = ('jwt_session_info', 'data_access_info', 'cli_access_info')

    def session_status(self, obj):
        """Affiche le statut de session JWT de l'utilisateur"""
        try:
            token_info = JWTAuthService.get_token_info()
            if token_info and token_info['username'] == obj.username:
                if token_info['is_expired']:
                    return format_html('<span style="color: red;">Session expiree</span>')
                else:
                    return format_html('<span style="color: green;">Session active</span>')
            else:
                return format_html('<span style="color: gray;">Pas de session</span>')
        except Exception:
            return format_html('<span style="color: gray;">Indetermine</span>')

    session_status.short_description = 'Statut JWT'

    def data_access(self, obj):
        """Affiche les statistiques d'acces aux donnees"""
        try:
            clients, _ = DataService.get_all_clients(obj)
            contracts, _ = DataService.get_all_contracts(obj)
            events, _ = DataService.get_all_events(obj)

            client_count = len(clients) if clients else 0
            contract_count = len(contracts) if contracts else 0
            event_count = len(events) if events else 0

            return format_html(
                'C:{} / Co:{} / E:{}',
                client_count, contract_count, event_count
            )
        except Exception:
            return format_html('<span style="color: red;">Erreur</span>')

    data_access.short_description = 'Acces donnees'

    def cli_access(self, obj):
        """Affiche le statut d'acces CLI"""
        try:
            token_info = JWTAuthService.get_token_info()
            if token_info and token_info['username'] == obj.username:
                return format_html('<span style="color: green;">CLI disponible</span>')
            else:
                return format_html('<span style="color: orange;">Connexion requise</span>')
        except Exception:
            return format_html('<span style="color: red;">Erreur CLI</span>')

    cli_access.short_description = 'Acces CLI'

    def jwt_session_info(self, obj):
        """Affiche les informations de session JWT detaillees"""
        try:
            token_info = JWTAuthService.get_token_info()
            if token_info and token_info['username'] == obj.username:
                status = "Expiree" if token_info['is_expired'] else "Active"
                return format_html(
                    '<strong>Statut:</strong> {}<br>'
                    '<strong>Expiration:</strong> {}<br>'
                    '<strong>Role dans le token:</strong> {}',
                    status,
                    token_info['expires_at'],
                    token_info['role']
                )
            else:
                return "Aucune session JWT active"
        except Exception as e:
            return f"Erreur: {e}"

    jwt_session_info.short_description = 'Informations session JWT'

    def data_access_info(self, obj):
        """Affiche les informations detaillees d'acces aux donnees"""
        try:
            clients, client_msg = DataService.get_all_clients(obj)
            contracts, contract_msg = DataService.get_all_contracts(obj)
            events, event_msg = DataService.get_all_events(obj)

            client_count = len(clients) if clients else 0
            contract_count = len(contracts) if contracts else 0
            event_count = len(events) if events else 0

            return format_html(
                '<strong>Clients accessibles:</strong> {} ({})<br>'
                '<strong>Contrats accessibles:</strong> {} ({})<br>'
                '<strong>Evenements accessibles:</strong> {} ({})<br>'
                '<strong>Restrictions:</strong> {}',
                client_count,
                'Tous' if obj.role == 'GESTION' else 'Seulement les siens',
                contract_count,
                'Tous' if obj.role == 'GESTION' else 'Seulement les siens',
                event_count,
                'Tous' if obj.role == 'GESTION' else 'Seulement les siens',
                'Aucune' if obj.role == 'GESTION' else f'Selon role {obj.role}'
            )
        except Exception as e:
            return f"Erreur lors de la recuperation des donnees: {e}"

    data_access_info.short_description = 'Informations acces aux donnees'

    def cli_access_info(self, obj):
        """Affiche les informations detaillees d'acces CLI"""
        try:
            token_info = JWTAuthService.get_token_info()
            if token_info and token_info['username'] == obj.username:
                commands_available = [
                    'clients', 'contracts', 'events', 'client <id>',
                    'contract <id>', 'event <id>', 'whoami', 'permissions'
                ]
                return format_html(
                    '<strong>Interface CLI:</strong> Disponible<br>'
                    '<strong>Commandes autorisees:</strong><br>'
                    '{}',
                    '<br>'.join([f'• python epicevents.py {cmd}' for cmd in commands_available])
                )
            else:
                return format_html(
                    '<strong>Interface CLI:</strong> Non disponible<br>'
                    '<strong>Connexion requise:</strong> python epicevents.py login {}<br>'
                    '<strong>Commandes disponibles apres connexion:</strong><br>'
                    '• Lecture des donnees selon les permissions du role {}',
                    obj.username,
                    obj.role
                )
        except Exception as e:
            return f"Erreur CLI: {e}"

    cli_access_info.short_description = 'Informations acces CLI'


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Administration des clients avec gestion des permissions"""

    list_display = ('company_name', 'first_name', 'last_name', 'email',
                    'sales_contact', 'contracts_count', 'created_at')
    list_filter = ('sales_contact', 'created_at')
    search_fields = ('company_name', 'first_name', 'last_name', 'email')

    fieldsets = (
        ('Informations client', {
            'fields': ('company_name', 'first_name', 'last_name', 'email')
        }),
        ('Contact', {
            'fields': ('phone', 'mobile')
        }),
        ('Gestion', {
            'fields': ('sales_contact',)
        }),
    )

    def contracts_count(self, obj):
        """Nombre de contrats pour ce client"""
        return obj.contracts.count()
    contracts_count.short_description = 'Contrats'


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    """Administration des contrats avec gestion des permissions"""

    list_display = ('id', 'client', 'sales_contact', 'total_amount',
                    'amount_due', 'is_signed', 'has_event', 'created_at')
    list_filter = ('is_signed', 'sales_contact', 'created_at')
    search_fields = ('client__company_name', 'client__last_name')

    fieldsets = (
        ('Informations contrat', {
            'fields': ('client', 'sales_contact')
        }),
        ('Montants', {
            'fields': ('total_amount', 'amount_due', 'is_signed')
        }),
    )

    def has_event(self, obj):
        """Indique si le contrat a un evenement"""
        try:
            event_exists = hasattr(obj, 'event') and obj.event
            if event_exists:
                return format_html('<span style="color: green;">Oui</span>')
            else:
                return format_html('<span style="color: red;">Non</span>')
        except Event.DoesNotExist:
            return format_html('<span style="color: red;">Non</span>')
    has_event.short_description = 'Evenement'


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Administration des evenements avec gestion des permissions"""

    list_display = ('name', 'client', 'support_contact', 'event_date_start',
                    'attendees', 'support_assigned', 'created_at')
    list_filter = ('support_contact', 'event_date_start', 'created_at')
    search_fields = ('name', 'contract__client__company_name')

    fieldsets = (
        ('Informations evenement', {
            'fields': ('name', 'contract', 'support_contact')
        }),
        ('Details', {
            'fields': ('event_date_start', 'event_date_end', 'location', 'attendees')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )

    def client(self, obj):
        """Affiche le client lie au contrat"""
        return obj.contract.client
    client.short_description = 'Client'

    def support_assigned(self, obj):
        """Indique si un support est assigne"""
        if obj.support_contact:
            return format_html('<span style="color: green;">Oui</span>')
        else:
            return format_html('<span style="color: orange;">Non assigne</span>')
    support_assigned.short_description = 'Support assigne'
