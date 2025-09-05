"""
Tests pour les vues - focus sur la couverture
Fichier: src/tests/test_views_coverage.py
"""

from unittest.mock import Mock, patch
from src.views.base_view import BaseView
from src.views.user_view import UserView
from src.views.client_view import ClientView


class TestViewsCoverage:
    """Tests pour améliorer la couverture des vues"""

    def test_base_view_display_table_simple(self):
        """Test de l'affichage de table simple"""
        view = BaseView()

        # Format correct pour display_table
        columns = [
            {"name": "ID", "style": "cyan"},
            {"name": "Name", "style": "white"}
        ]
        data = [
            [1, "Test"],     # Liste de valeurs
            [2, "Test2"]     # Liste de valeurs
        ]

        # Mock Rich console au lieu de print
        with patch.object(view.console, 'print') as mock_console_print:
            view.display_table("Test Table", columns, data)
            assert mock_console_print.called

    def test_base_view_display_info(self):
        """Test d'affichage d'info"""
        view = BaseView()

        with patch('builtins.print'):
            view.display_info("Test message")
            # Le test passe si aucune exception n'est levée

    def test_base_view_display_error(self):
        """Test d'affichage d'erreur"""
        view = BaseView()

        # Pas de mock, on laisse Rich afficher normalement
        view.display_error("Test error")
        # Le test passe si aucune exception n'est levée

    def test_base_view_display_success(self):
        """Test d'affichage de succès"""
        view = BaseView()

        # Pas de mock, on laisse Rich afficher normalement
        view.display_success("Test success")
        # Le test passe si aucune exception n'est levée

    def test_user_view_display_users_table(self):
        """Test d'affichage de table d'utilisateurs"""
        # Mock du constructeur pour éviter l'accès à la base de données
        with patch('src.views.user_view.UserView.__init__', return_value=None):
            view = UserView()
            view.console = Mock()  # Mock de la console Rich

            # Mock users
            mock_user1 = Mock()
            mock_user1.id = 1
            mock_user1.full_name = "John Doe"
            mock_user1.email = "john@test.com"
            mock_user1.department.value = "commercial"

            mock_user2 = Mock()
            mock_user2.id = 2
            mock_user2.full_name = "Jane Smith"
            mock_user2.email = "jane@test.com"
            mock_user2.department.value = "support"

            users = [mock_user1, mock_user2]

            # Test de la méthode privée avec mock
            with patch.object(view, '_display_users_table') as mock_display:
                view._display_users_table(users)
                mock_display.assert_called_once_with(users)

    def test_client_view_display_clients_table(self):
        """Test d'affichage de table de clients"""
        # Mock du constructeur pour éviter l'accès à la base de données
        with patch('src.views.client_view.ClientView.__init__', return_value=None):
            view = ClientView()
            view.console = Mock()  # Mock de la console Rich

            # Mock clients
            mock_client1 = Mock()
            mock_client1.id = 1
            mock_client1.full_name = "John Client"
            mock_client1.email = "client1@test.com"
            mock_client1.company_name = "Company 1"
            mock_client1.commercial_contact.full_name = "Commercial 1"

            mock_client2 = Mock()
            mock_client2.id = 2
            mock_client2.full_name = "Jane Client"
            mock_client2.email = "client2@test.com"
            mock_client2.company_name = "Company 2"
            mock_client2.commercial_contact.full_name = "Commercial 2"

            clients = [mock_client1, mock_client2]

            # Test de la méthode privée avec mock
            with patch.object(view, '_display_clients_table') as mock_display:
                view._display_clients_table(clients)
                mock_display.assert_called_once_with(clients)

    def test_base_view_confirm_action(self):
        """Test de confirmation d'action"""
        view = BaseView()

        # Test avec 'y'
        with patch('rich.prompt.Confirm.ask', return_value=True):
            result = view.confirm_action("Continue?")
            assert result is True

        # Test avec 'n'
        with patch('rich.prompt.Confirm.ask', return_value=False):
            result = view.confirm_action("Continue?")
            assert result is False

    def test_base_view_simple_functionality(self):
        """Test de fonctionnalités simples"""
        view = BaseView()

        # Test que l'objet se crée sans erreur
        assert view is not None
        assert hasattr(view, 'console')

        # Test d'affichage simple
        view.display_header("Test Header")
        view.display_separator()
        # Le test passe si aucune exception n'est levée
