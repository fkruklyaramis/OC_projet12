from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Administration des utilisateurs personnalisés"""

    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'employee_number', 'is_active')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'employee_number', 'first_name', 'last_name')

    fieldsets = UserAdmin.fieldsets + (
        ('Informations Epic Events', {
            'fields': ('role', 'employee_number')
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations Epic Events', {
            'fields': ('role', 'employee_number')
        }),
    )
