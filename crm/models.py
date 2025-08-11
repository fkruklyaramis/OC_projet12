from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator


class User(AbstractUser):
    """Modèle utilisateur personnalisé pour les collaborateurs Epic Events"""

    ROLE_CHOICES = [
        ('COMMERCIAL', 'Commercial'),
        ('SUPPORT', 'Support'),
        ('GESTION', 'Gestion'),
    ]

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        verbose_name="Rôle"
    )
    employee_number = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="Numéro d'employé"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.role})"


class Client(models.Model):
    """Modèle pour les clients d'Epic Events"""

    company_name = models.CharField(
        max_length=250,
        verbose_name="Nom de l'entreprise"
    )
    first_name = models.CharField(
        max_length=25,
        verbose_name="Prénom"
    )
    last_name = models.CharField(
        max_length=25,
        verbose_name="Nom"
    )
    email = models.EmailField(
        verbose_name="Email"
    )
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Le numéro de téléphone doit être au format: '+999999999'. 15 chiffres maximum."
    )
    phone = models.CharField(
        validators=[phone_regex],
        max_length=17,
        verbose_name="Téléphone"
    )
    mobile = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        verbose_name="Mobile"
    )

    # Relation avec le commercial responsable
    sales_contact = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'role': 'COMMERCIAL'},
        related_name='clients',
        verbose_name="Contact commercial"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"

    def __str__(self):
        return f"{self.company_name} - {self.first_name} {self.last_name}"


class Contract(models.Model):
    """Modèle pour les contrats"""

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='contracts',
        verbose_name="Client"
    )
    sales_contact = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'role': 'COMMERCIAL'},
        related_name='contracts',
        verbose_name="Contact commercial"
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Montant total"
    )
    amount_due = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Montant restant à payer"
    )
    is_signed = models.BooleanField(
        default=False,
        verbose_name="Contrat signé"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Contrat"
        verbose_name_plural = "Contrats"

    def __str__(self):
        return f"Contrat #{self.id} - {self.client.company_name}"

    @property
    def is_fully_paid(self):
        """Vérifie si le contrat est entièrement payé"""
        return self.amount_due == 0


class Event(models.Model):
    """Modèle pour les événements"""

    contract = models.OneToOneField(
        Contract,
        on_delete=models.CASCADE,
        related_name='event',
        verbose_name="Contrat"
    )
    name = models.CharField(
        max_length=150,
        verbose_name="Nom de l'événement"
    )
    support_contact = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'SUPPORT'},
        related_name='events',
        verbose_name="Contact support"
    )
    event_date_start = models.DateTimeField(
        verbose_name="Date de début"
    )
    event_date_end = models.DateTimeField(
        verbose_name="Date de fin"
    )
    location = models.TextField(
        verbose_name="Lieu"
    )
    attendees = models.PositiveIntegerField(
        verbose_name="Nombre de participants"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Notes"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Événement"
        verbose_name_plural = "Événements"

    def __str__(self):
        return f"{self.name} - {self.contract.client.company_name}"

    @property
    def client(self):
        """Accès rapide au client via le contrat"""
        return self.contract.client
