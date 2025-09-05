import re
from datetime import datetime
from src.models.user import Department
from src.models.contract import ContractStatus
from decimal import Decimal
from src.config.messages import VALIDATION_MESSAGES


class ValidationError(Exception):
    """Exception pour les erreurs de validation"""
    pass


class DataValidator:
    """Classe pour la validation des données"""

    @staticmethod
    def validate_email(email: str) -> str:
        """Valider un email"""
        if not email:
            raise ValidationError(VALIDATION_MESSAGES["email_required"])

        email = email.strip().lower()
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not re.match(email_pattern, email):
            raise ValidationError(VALIDATION_MESSAGES["email_invalid_format"])

        if len(email) > 255:
            raise ValidationError(VALIDATION_MESSAGES["email_too_long"])

        return email

    @staticmethod
    def validate_phone(phone: str) -> str:
        """Valider un numéro de téléphone"""
        if not phone:
            raise ValidationError(VALIDATION_MESSAGES["phone_required"])

        phone = phone.strip()
        # Format français : 01.23.45.67.89 ou 0123456789
        phone_pattern = r'^(0[1-9](\.[0-9]{2}){4}|0[1-9][0-9]{8})$'

        if not re.match(phone_pattern, phone):
            raise ValidationError(VALIDATION_MESSAGES["phone_invalid_format"])

        return phone

    @staticmethod
    def validate_employee_number(employee_number: str) -> str:
        """Valider un numéro d'employé"""
        if not employee_number:
            raise ValidationError(VALIDATION_MESSAGES["employee_number_required"])

        employee_number = employee_number.strip().upper()
        # Format : EE000001
        pattern = r'^EE[0-9]{6}$'

        if not re.match(pattern, employee_number):
            raise ValidationError(VALIDATION_MESSAGES["employee_number_invalid_format"])

        return employee_number

    @staticmethod
    def validate_full_name(full_name: str) -> str:
        """Valider un nom complet"""
        if not full_name:
            raise ValidationError(VALIDATION_MESSAGES["full_name_required"])

        full_name = full_name.strip()

        if len(full_name) < 2:
            raise ValidationError(VALIDATION_MESSAGES["full_name_too_short"])

        if len(full_name) > 255:
            raise ValidationError(VALIDATION_MESSAGES["full_name_too_long"])

        # Vérifier que le nom contient au moins un prénom et un nom
        parts = full_name.split()
        if len(parts) < 2:
            raise ValidationError(VALIDATION_MESSAGES["full_name_incomplete"])

        return full_name

    @staticmethod
    def validate_company_name(company_name: str) -> str:
        """Valider un nom d'entreprise"""
        if not company_name:
            raise ValidationError(VALIDATION_MESSAGES["company_name_required"])

        company_name = company_name.strip()

        if len(company_name) < 2:
            raise ValidationError(VALIDATION_MESSAGES["company_name_too_short"])

        if len(company_name) > 255:
            raise ValidationError(VALIDATION_MESSAGES["company_name_too_long"])

        return company_name

    @staticmethod
    def validate_department(department: str) -> Department:
        """Valider un département"""
        if not department:
            raise ValidationError(VALIDATION_MESSAGES["department_required"])

        department = department.strip().lower()

        try:
            return Department(department)
        except ValueError:
            valid_departments = [d.value for d in Department]
            raise ValidationError(
                VALIDATION_MESSAGES["department_invalid"].format(
                    departments=', '.join(valid_departments)
                )
            )

    @staticmethod
    def validate_amount(amount: float, field_name: str = "Montant") -> float:
        """Valider un montant"""
        if amount is None:
            raise ValidationError(VALIDATION_MESSAGES["amount_required"].format(field=field_name))

        if not isinstance(amount, (int, float, Decimal)):
            raise ValidationError(VALIDATION_MESSAGES["amount_must_be_number"].format(field=field_name))

        amount = float(amount)

        if amount < 0:
            raise ValidationError(VALIDATION_MESSAGES["amount_negative"].format(field=field_name))

        if amount > 999999999.99:
            raise ValidationError(VALIDATION_MESSAGES["amount_too_large"].format(field=field_name))

        # Arrondir à 2 décimales
        return round(amount, 2)

    @staticmethod
    def validate_contract_status(status: str) -> ContractStatus:
        """Valider un statut de contrat"""
        if not status:
            raise ValidationError(VALIDATION_MESSAGES["status_required"])

        status = status.strip().lower()

        try:
            return ContractStatus(status)
        except ValueError:
            valid_statuses = [s.value for s in ContractStatus]
            raise ValidationError(
                VALIDATION_MESSAGES["status_invalid"].format(
                    statuses=', '.join(valid_statuses)
                )
            )

    @staticmethod
    def validate_date_range(start_date: datetime, end_date: datetime):
        """Valider une plage de dates"""
        if not start_date:
            raise ValidationError(VALIDATION_MESSAGES["start_date_required"])

        if not end_date:
            raise ValidationError(VALIDATION_MESSAGES["end_date_required"])

        if start_date >= end_date:
            raise ValidationError(VALIDATION_MESSAGES["end_date_before_start"])

        # Vérifier que l'événement n'est pas dans le passé (sauf pour les tests)
        if start_date < datetime.now():
            raise ValidationError(VALIDATION_MESSAGES["start_date_past"])

    @staticmethod
    def validate_attendees_count(attendees: int) -> int:
        """Valider le nombre de participants"""
        if attendees is None:
            raise ValidationError(VALIDATION_MESSAGES["attendees_required"])

        if not isinstance(attendees, int):
            raise ValidationError(VALIDATION_MESSAGES["attendees_must_be_integer"])

        if attendees <= 0:
            raise ValidationError(VALIDATION_MESSAGES["attendees_positive"])

        if attendees > 10000:
            raise ValidationError(VALIDATION_MESSAGES["attendees_too_large"])

        return attendees

    @staticmethod
    def validate_event_name(name: str) -> str:
        """Valider un nom d'événement"""
        if not name:
            raise ValidationError(VALIDATION_MESSAGES["event_name_required"])

        name = name.strip()

        if len(name) < 3:
            raise ValidationError(VALIDATION_MESSAGES["event_name_too_short"])

        if len(name) > 255:
            raise ValidationError(VALIDATION_MESSAGES["event_name_too_long"])

        return name

    @staticmethod
    def validate_location(location: str) -> str:
        """Valider un lieu"""
        if not location:
            raise ValidationError(VALIDATION_MESSAGES["location_required"])

        location = location.strip()

        if len(location) < 3:
            raise ValidationError(VALIDATION_MESSAGES["location_too_short"])

        if len(location) > 255:
            raise ValidationError(VALIDATION_MESSAGES["location_too_long"])

        return location
