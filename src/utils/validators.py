import re
from datetime import datetime
from src.models.user import Department
from src.models.contract import ContractStatus


class ValidationError(Exception):
    """Exception pour les erreurs de validation"""
    pass


class DataValidator:
    """Classe pour la validation des données"""

    @staticmethod
    def validate_email(email: str) -> str:
        """Valider un email"""
        if not email:
            raise ValidationError("L'email est requis")

        email = email.strip().lower()
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not re.match(email_pattern, email):
            raise ValidationError("Format d'email invalide")

        if len(email) > 255:
            raise ValidationError("L'email ne peut pas dépasser 255 caractères")

        return email

    @staticmethod
    def validate_phone(phone: str) -> str:
        """Valider un numéro de téléphone"""
        if not phone:
            raise ValidationError("Le numéro de téléphone est requis")

        phone = phone.strip()
        # Format français : 01.23.45.67.89 ou 0123456789
        phone_pattern = r'^(0[1-9](\.[0-9]{2}){4}|0[1-9][0-9]{8})$'

        if not re.match(phone_pattern, phone):
            raise ValidationError("Format de téléphone invalide (exemple: 01.23.45.67.89)")

        return phone

    @staticmethod
    def validate_employee_number(employee_number: str) -> str:
        """Valider un numéro d'employé"""
        if not employee_number:
            raise ValidationError("Le numéro d'employé est requis")

        employee_number = employee_number.strip().upper()
        # Format : EE000001
        pattern = r'^EE[0-9]{6}$'

        if not re.match(pattern, employee_number):
            raise ValidationError("Format de numéro d'employé invalide (exemple: EE000001)")

        return employee_number

    @staticmethod
    def validate_full_name(full_name: str) -> str:
        """Valider un nom complet"""
        if not full_name:
            raise ValidationError("Le nom complet est requis")

        full_name = full_name.strip()

        if len(full_name) < 2:
            raise ValidationError("Le nom complet doit contenir au moins 2 caractères")

        if len(full_name) > 255:
            raise ValidationError("Le nom complet ne peut pas dépasser 255 caractères")

        # Vérifier que le nom contient au moins un prénom et un nom
        parts = full_name.split()
        if len(parts) < 2:
            raise ValidationError("Le nom complet doit contenir prénom et nom")

        return full_name

    @staticmethod
    def validate_company_name(company_name: str) -> str:
        """Valider un nom d'entreprise"""
        if not company_name:
            raise ValidationError("Le nom de l'entreprise est requis")

        company_name = company_name.strip()

        if len(company_name) < 2:
            raise ValidationError("Le nom de l'entreprise doit contenir au moins 2 caractères")

        if len(company_name) > 255:
            raise ValidationError("Le nom de l'entreprise ne peut pas dépasser 255 caractères")

        return company_name

    @staticmethod
    def validate_department(department: str) -> Department:
        """Valider un département"""
        if not department:
            raise ValidationError("Le département est requis")

        department = department.strip().lower()

        try:
            return Department(department)
        except ValueError:
            valid_departments = [d.value for d in Department]
            raise ValidationError(
                f"Département invalide. Valeurs autorisées: {', '.join(valid_departments)}"
            )

    @staticmethod
    def validate_amount(amount: float, field_name: str = "Montant") -> float:
        """Valider un montant"""
        if amount is None:
            raise ValidationError(f"{field_name} est requis")

        if not isinstance(amount, (int, float)):
            raise ValidationError(f"{field_name} doit être un nombre")

        amount = float(amount)

        if amount < 0:
            raise ValidationError(f"{field_name} ne peut pas être négatif")

        if amount > 999999999.99:
            raise ValidationError(f"{field_name} ne peut pas dépasser 999,999,999.99")

        # Arrondir à 2 décimales
        return round(amount, 2)

    @staticmethod
    def validate_contract_status(status: str) -> ContractStatus:
        """Valider un statut de contrat"""
        if not status:
            raise ValidationError("Le statut est requis")

        status = status.strip().lower()

        try:
            return ContractStatus(status)
        except ValueError:
            valid_statuses = [s.value for s in ContractStatus]
            raise ValidationError(
                f"Statut invalide. Valeurs autorisées: {', '.join(valid_statuses)}"
            )

    @staticmethod
    def validate_date_range(start_date: datetime, end_date: datetime):
        """Valider une plage de dates"""
        if not start_date:
            raise ValidationError("La date de début est requise")

        if not end_date:
            raise ValidationError("La date de fin est requise")

        if start_date >= end_date:
            raise ValidationError("La date de fin doit être postérieure à la date de début")

        # Vérifier que l'événement n'est pas dans le passé (sauf pour les tests)
        if start_date < datetime.now():
            raise ValidationError("La date de début ne peut pas être dans le passé")

    @staticmethod
    def validate_attendees_count(attendees: int) -> int:
        """Valider le nombre de participants"""
        if attendees is None:
            raise ValidationError("Le nombre de participants est requis")

        if not isinstance(attendees, int):
            raise ValidationError("Le nombre de participants doit être un entier")

        if attendees <= 0:
            raise ValidationError("Le nombre de participants doit être supérieur à 0")

        if attendees > 10000:
            raise ValidationError("Le nombre de participants ne peut pas dépasser 10,000")

        return attendees

    @staticmethod
    def validate_event_name(name: str) -> str:
        """Valider un nom d'événement"""
        if not name:
            raise ValidationError("Le nom de l'événement est requis")

        name = name.strip()

        if len(name) < 3:
            raise ValidationError("Le nom de l'événement doit contenir au moins 3 caractères")

        if len(name) > 255:
            raise ValidationError("Le nom de l'événement ne peut pas dépasser 255 caractères")

        return name

    @staticmethod
    def validate_location(location: str) -> str:
        """Valider un lieu"""
        if not location:
            raise ValidationError("Le lieu est requis")

        location = location.strip()

        if len(location) < 3:
            raise ValidationError("Le lieu doit contenir au moins 3 caractères")

        if len(location) > 255:
            raise ValidationError("Le lieu ne peut pas dépasser 255 caractères")

        return location
