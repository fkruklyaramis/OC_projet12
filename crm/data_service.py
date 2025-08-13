"""Service de lecture de données avec gestion des permissions"""
from django.contrib.auth import get_user_model
from .models import Client, Contract, Event
from .auth import PermissionService

User = get_user_model()


class DataService:
    """Service pour la lecture de données avec contrôle des permissions"""

    @staticmethod
    def get_all_clients(user):
        """
        Récupère tous les clients selon les permissions de l'utilisateur
        """
        if not PermissionService.can_view_all_clients(user):
            return None, "Permission refusée pour consulter les clients"

        try:
            if user.role == 'COMMERCIAL':
                # Commercial ne voit que ses clients
                clients = Client.objects.filter(sales_contact=user).select_related('sales_contact')
            else:
                # Support et Gestion voient tous les clients
                clients = Client.objects.all().select_related('sales_contact')

            return list(clients), f"{len(clients)} clients trouvés"

        except Exception as e:
            return None, f"Erreur lors de la récupération des clients: {e}"

    @staticmethod
    def get_all_contracts(user):
        """
        Récupère tous les contrats selon les permissions de l'utilisateur
        """
        if not PermissionService.can_view_all_contracts(user):
            return None, "Permission refusée pour consulter les contrats"

        try:
            if user.role == 'COMMERCIAL':
                # Commercial ne voit que ses contrats
                contracts = Contract.objects.filter(
                    sales_contact=user
                ).select_related('client', 'sales_contact')
            else:
                # Support et Gestion voient tous les contrats
                contracts = Contract.objects.all().select_related('client', 'sales_contact')

            return list(contracts), f"{len(contracts)} contrats trouvés"

        except Exception as e:
            return None, f"Erreur lors de la récupération des contrats: {e}"

    @staticmethod
    def get_all_events(user):
        """
        Récupère tous les événements selon les permissions de l'utilisateur
        """
        if not PermissionService.can_view_all_events(user):
            return None, "Permission refusée pour consulter les événements"

        try:
            if user.role == 'SUPPORT':
                # Support ne voit que ses événements
                events = Event.objects.filter(
                    support_contact=user
                ).select_related('contract__client', 'support_contact')
            elif user.role == 'COMMERCIAL':
                # Commercial voit les événements de ses contrats
                events = Event.objects.filter(
                    contract__sales_contact=user
                ).select_related('contract__client', 'support_contact')
            else:
                # Gestion voit tous les événements
                events = Event.objects.all().select_related('contract__client', 'support_contact')

            return list(events), f"{len(events)} événements trouvés"

        except Exception as e:
            return None, f"Erreur lors de la récupération des événements: {e}"

    @staticmethod
    def get_client_by_id(user, client_id):
        """Récupère un client spécifique selon les permissions"""
        if not PermissionService.can_view_all_clients(user):
            return None, "Permission refusée pour consulter les clients"

        try:
            if user.role == 'COMMERCIAL':
                client = Client.objects.select_related('sales_contact').get(
                    id=client_id, sales_contact=user
                )
            else:
                client = Client.objects.select_related('sales_contact').get(id=client_id)

            return client, "Client trouvé"

        except Client.DoesNotExist:
            return None, "Client non trouvé ou accès refusé"
        except Exception as e:
            return None, f"Erreur lors de la récupération du client: {e}"

    @staticmethod
    def get_contract_by_id(user, contract_id):
        """Récupère un contrat spécifique selon les permissions"""
        if not PermissionService.can_view_all_contracts(user):
            return None, "Permission refusée pour consulter les contrats"

        try:
            if user.role == 'COMMERCIAL':
                contract = Contract.objects.select_related('client', 'sales_contact').get(
                    id=contract_id, sales_contact=user
                )
            else:
                contract = Contract.objects.select_related('client', 'sales_contact').get(
                    id=contract_id
                )

            return contract, "Contrat trouvé"

        except Contract.DoesNotExist:
            return None, "Contrat non trouvé ou accès refusé"
        except Exception as e:
            return None, f"Erreur lors de la récupération du contrat: {e}"

    @staticmethod
    def get_event_by_id(user, event_id):
        """Récupère un événement spécifique selon les permissions"""
        if not PermissionService.can_view_all_events(user):
            return None, "Permission refusée pour consulter les événements"

        try:
            base_query = Event.objects.select_related('contract__client', 'support_contact')

            if user.role == 'SUPPORT':
                event = base_query.get(id=event_id, support_contact=user)
            elif user.role == 'COMMERCIAL':
                event = base_query.get(id=event_id, contract__sales_contact=user)
            else:
                event = base_query.get(id=event_id)

            return event, "Événement trouvé"

        except Event.DoesNotExist:
            return None, "Événement non trouvé ou accès refusé"
        except Exception as e:
            return None, f"Erreur lors de la récupération de l'événement: {e}"

    @staticmethod
    def get_filtered_clients(user, **filters):
        """Récupère des clients avec des filtres"""
        if not PermissionService.can_view_all_clients(user):
            return None, "Permission refusée pour consulter les clients"

        try:
            queryset = Client.objects.select_related('sales_contact')

            # Appliquer les restrictions selon le rôle
            if user.role == 'COMMERCIAL':
                queryset = queryset.filter(sales_contact=user)

            # Appliquer les filtres fournis
            if 'company_name' in filters:
                queryset = queryset.filter(company_name__icontains=filters['company_name'])
            if 'email' in filters:
                queryset = queryset.filter(email__icontains=filters['email'])
            if 'sales_contact_id' in filters:
                queryset = queryset.filter(sales_contact_id=filters['sales_contact_id'])

            clients = list(queryset)
            return clients, f"{len(clients)} clients trouvés avec les filtres"

        except Exception as e:
            return None, f"Erreur lors de la recherche de clients: {e}"

    @staticmethod
    def get_filtered_contracts(user, **filters):
        """Récupère des contrats avec des filtres"""
        if not PermissionService.can_view_all_contracts(user):
            return None, "Permission refusée pour consulter les contrats"

        try:
            queryset = Contract.objects.select_related('client', 'sales_contact')

            # Appliquer les restrictions selon le rôle
            if user.role == 'COMMERCIAL':
                queryset = queryset.filter(sales_contact=user)

            # Appliquer les filtres fournis
            if 'is_signed' in filters:
                queryset = queryset.filter(is_signed=filters['is_signed'])
            if 'client_id' in filters:
                queryset = queryset.filter(client_id=filters['client_id'])
            if 'min_amount' in filters:
                queryset = queryset.filter(total_amount__gte=filters['min_amount'])

            contracts = list(queryset)
            return contracts, f"{len(contracts)} contrats trouvés avec les filtres"

        except Exception as e:
            return None, f"Erreur lors de la recherche de contrats: {e}"

    @staticmethod
    def get_filtered_events(user, **filters):
        """Récupère des événements avec des filtres"""
        if not PermissionService.can_view_all_events(user):
            return None, "Permission refusée pour consulter les événements"

        try:
            queryset = Event.objects.select_related('contract__client', 'support_contact')

            # Appliquer les restrictions selon le rôle
            if user.role == 'SUPPORT':
                queryset = queryset.filter(support_contact=user)
            elif user.role == 'COMMERCIAL':
                queryset = queryset.filter(contract__sales_contact=user)

            # Appliquer les filtres fournis
            if 'support_contact_id' in filters:
                queryset = queryset.filter(support_contact_id=filters['support_contact_id'])
            if 'date_start' in filters:
                queryset = queryset.filter(event_date_start__gte=filters['date_start'])
            if 'date_end' in filters:
                queryset = queryset.filter(event_date_end__lte=filters['date_end'])

            events = list(queryset)
            return events, f"{len(events)} événements trouvés avec les filtres"

        except Exception as e:
            return None, f"Erreur lors de la recherche d'événements: {e}"
