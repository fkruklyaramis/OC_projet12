from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from .models import Client, Contract, Event
from .jwt_auth import JWTAuthService

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Administration des utilisateurs Epic Events avec informations de session"""

    list_display = ('username', 'employee_number', 'first_name', 'last_name',
                    'email', 'role', 'is_active', 'session_status', 'date_joined')
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
            'description': 'Numéro d\'employé unique et affiliation au département'
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
            'description': 'Numéro d\'employé unique et département'
        }),
    )

    readonly_fields = ('jwt_session_info',)

    def session_status(self, obj):
        """Affiche le statut de session JWT de l'utilisateur"""
        try:
            token_info = JWTAuthService.get_token_info()
            if token_info and token_info['username'] == obj.username:
                if token_info['is_expired']:
                    return format_html('<span style="color: red;">Session expirée</span>')
                else:
                    return format_html('<span style="color: green;">Session active</span>')
            else:
                return format_html('<span style="color: gray;">Pas de session</span>')
        except Exception:
            return format_html('<span style="color: gray;">Indéterminé</span>')

    session_status.short_description = 'Statut JWT'

    def jwt_session_info(self, obj):
        """Affiche les informations de session JWT détaillées"""
        try:
            token_info = JWTAuthService.get_token_info()
            if token_info and token_info['username'] == obj.username:
                status = "Expirée" if token_info['is_expired'] else "Active"
                return format_html(
                    '<strong>Statut:</strong> {}<br>'
                    '<strong>Expiration:</strong> {}<br>'
                    '<strong>Rôle dans le token:</strong> {}',
                    status,
                    token_info['expires_at'],
                    token_info['role']
                )
            else:
                return "Aucune session JWT active"
        except Exception as e:
            return f"Erreur: {e}"

    jwt_session_info.short_description = 'Informations session JWT'


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Administration des clients"""

    list_display = ('company_name', 'first_name', 'last_name', 'email',
                    'sales_contact', 'created_at')
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


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    """Administration des contrats"""

    list_display = ('id', 'client', 'sales_contact', 'total_amount',
                    'amount_due', 'is_signed', 'created_at')
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


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Administration des événements"""

    list_display = ('name', 'client', 'support_contact', 'event_date_start',
                    'attendees', 'created_at')
    list_filter = ('support_contact', 'event_date_start', 'created_at')
    search_fields = ('name', 'contract__client__company_name')

    fieldsets = (
        ('Informations événement', {
            'fields': ('name', 'contract', 'support_contact')
        }),
        ('Détails', {
            'fields': ('event_date_start', 'event_date_end', 'location', 'attendees')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )

    def client(self, obj):
        """Affiche le client lié au contrat"""
        return obj.contract.client
    client.short_description = 'Client'
