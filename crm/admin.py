from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from .models import Client, Contract, Event

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Administration des utilisateurs Epic Events avec tous les champs requis"""

    # Affichage dans la liste
    list_display = ('username', 'employee_number', 'first_name', 'last_name',
                    'email', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'employee_number', 'first_name', 'last_name')
    ordering = ('employee_number',)

    # Champs lors de la modification d'un utilisateur existant
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
        ('Dates importantes', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )

    # Champs lors de la création d'un nouvel utilisateur
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
