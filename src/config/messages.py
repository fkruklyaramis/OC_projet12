"""
Fichier de configuration pour centraliser tous les messages CLI
Fichier: src/config/messages.py
"""

# ===== MESSAGES D'AUTHENTIFICATION =====
AUTH_MESSAGES = {
    'login_header': "CONNEXION EPIC EVENTS CRM",
    'logout_header': "DÉCONNEXION",
    'status_header': "STATUT DE CONNEXION",
    'login_success': "Connexion réussie",
    'logout_success': "Déconnexion réussie",
    'auth_required': "Authentification requise",
    'user_not_found': "Utilisateur non trouvé",
    'incorrect_password': "Mot de passe incorrect",
    'not_connected': "Vous n'êtes pas connecté",
}

# ===== MESSAGES UTILISATEURS =====
USER_MESSAGES = {
    'create_header': "CRÉATION D'UN NOUVEAU COLLABORATEUR",
    'list_header': "TOUS LES COLLABORATEURS",
    'update_header': "MODIFICATION D'UN COLLABORATEUR",
    'delete_header': "SUPPRESSION D'UN COLLABORATEUR",
    'search_header': "RECHERCHE DE COLLABORATEURS",
    'password_change_header': "CHANGEMENT DE MOT DE PASSE",
    'create_success': "Utilisateur créé avec succès",
    'update_success': "Utilisateur mis à jour avec succès",
    'delete_success': "Utilisateur supprimé avec succès",
    'password_change_success': "Mot de passe changé avec succès",
    'user_not_found': "Utilisateur non trouvé",
    'no_users_found': "Aucun collaborateur trouvé",
}

# ===== MESSAGES CLIENTS =====
CLIENT_MESSAGES = {
    'create_header': "CRÉATION D'UN NOUVEAU CLIENT",
    'list_header': "TOUS LES CLIENTS",
    'my_clients_header': "MES CLIENTS",
    'update_header': "MODIFICATION D'UN CLIENT",
    'delete_header': "SUPPRESSION D'UN CLIENT",
    'search_header': "RECHERCHE DE CLIENTS",
    'create_success': "Client créé avec succès",
    'update_success': "Client mis à jour avec succès",
    'delete_success': "Client supprimé avec succès",
    'client_not_found': "Client non trouvé",
    'no_clients_found': "Aucun client trouvé",
    'no_commercials_available': "Aucun commercial disponible",
    'commercial_required': "Vous devez spécifier un commercial responsable",
}

# ===== MESSAGES CONTRATS =====
CONTRACT_MESSAGES = {
    'create_header': "CRÉATION D'UN NOUVEAU CONTRAT",
    'list_header': "TOUS LES CONTRATS",
    'my_contracts_header': "MES CONTRATS",
    'update_header': "MODIFICATION D'UN CONTRAT",
    'search_header': "RECHERCHE DE CONTRATS",
    'create_success': "Contrat créé avec succès",
    'update_success': "Contrat mis à jour avec succès",
    'sign_success': "Contrat signé avec succès",
    'contract_not_found': "Contrat non trouvé",
    'no_contracts_found': "Aucun contrat trouvé",
}

# ===== MESSAGES ÉVÉNEMENTS =====
EVENT_MESSAGES = {
    'create_header': "CRÉATION D'UN NOUVEL ÉVÉNEMENT",
    'list_header': "TOUS LES ÉVÉNEMENTS",
    'my_events_header': "MES ÉVÉNEMENTS",
    'update_header': "MODIFICATION D'UN ÉVÉNEMENT",
    'search_header': "RECHERCHE D'ÉVÉNEMENTS",
    'create_success': "Événement créé avec succès",
    'update_success': "Événement mis à jour avec succès",
    'assign_success': "Support assigné avec succès",
    'event_not_found': "Événement non trouvé",
    'no_events_found': "Aucun événement trouvé",
    'no_support_available': "Aucun utilisateur support disponible",
}

# ===== MESSAGES DE VALIDATION =====
VALIDATION_MESSAGES = {
    'email_invalid': "Format d'email invalide",
    'email_required': "L'email est obligatoire",
    'phone_invalid': "Format de téléphone invalide",
    'name_required': "Le nom est obligatoire",
    'password_required': "Le mot de passe est obligatoire",
    'amount_invalid': "Montant invalide",
    'date_invalid': "Format de date invalide",
    'field_required': "Ce champ est obligatoire",
}

# ===== MESSAGES GÉNÉRAUX =====
GENERAL_MESSAGES = {
    'operation_cancelled': "Opération annulée",
    'no_changes_made': "Aucune modification apportée",
    'no_search_criteria': "Aucun critère de recherche fourni",
    'access_denied': "Accès refusé",
    'unauthorized': "Action non autorisée",
    'loading': "Chargement...",
    'processing': "Traitement en cours...",
}

# ===== PROMPTS UTILISATEUR =====
PROMPTS = {
    'email': "Email",
    'password': "Mot de passe",
    'name': "Nom complet",
    'phone': "Téléphone",
    'company': "Entreprise",
    'amount': "Montant",
    'date': "Date (YYYY-MM-DD)",
    'location': "Lieu",
    'attendees': "Nombre de participants",
    'name_optional': "Nom (optionnel)",
    'email_optional': "Email (optionnel)",
    'company_optional': "Entreprise (optionnel)",
}

# ===== CONFIRMATIONS =====
CONFIRMATIONS = {
    'delete_user': "Êtes-vous sûr de vouloir supprimer cet utilisateur ?",
    'delete_client': "Êtes-vous sûr de vouloir supprimer ce client ?",
    'delete_contract': "Êtes-vous sûr de vouloir supprimer ce contrat ?",
    'delete_event': "Êtes-vous sûr de vouloir supprimer cet événement ?",
    'sign_contract': "Êtes-vous sûr de vouloir signer ce contrat ?",
    'change_password': "Changer le mot de passe ?",
    'change_department': "Changer le département ?",
    'change_commercial': "Changer le commercial responsable ?",
}
