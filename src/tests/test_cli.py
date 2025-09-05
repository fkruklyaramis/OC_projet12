"""
Tests pour l'interface en ligne de commande (CLI)
Fichier: src/tests/test_cli.py
"""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
import tempfile
import os
from src.database.init_db import init_database


class TestCLI:
    """Tests pour l'interface en ligne de commande"""

    def test_cli_help(self):
        """Test de l'affichage de l'aide"""
        from epicevents import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert "Epic Events CRM" in result.output
        assert "Système de gestion des événements" in result.output

    def test_init_command_success(self, monkeypatch, mock_env_vars):
        """Test de la commande d'initialisation"""
        from epicevents import init
        
        # Créer une base de données temporaire
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        
        try:
            monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
            
            runner = CliRunner()
            
            with patch('src.database.init_db.print') as mock_print:
                result = runner.invoke(init)
            
            assert result.exit_code == 0
            assert "Base de données initialisée avec succès" in result.output
            
        finally:
            os.close(db_fd)
            os.unlink(db_path)

    def test_login_command_help(self):
        """Test de l'aide de la commande login"""
        from epicevents import login
        
        runner = CliRunner()
        result = runner.invoke(login, ['--help'])
        
        assert result.exit_code == 0
        assert "Se connecter" in result.output

    def test_logout_command_help(self):
        """Test de l'aide de la commande logout"""
        from epicevents import logout
        
        runner = CliRunner()
        result = runner.invoke(logout, ['--help'])
        
        assert result.exit_code == 0
        assert "Se déconnecter" in result.output

    def test_status_command_help(self):
        """Test de l'aide de la commande status"""
        from epicevents import status
        
        runner = CliRunner()
        result = runner.invoke(status, ['--help'])
        
        assert result.exit_code == 0

    def test_user_commands_help(self):
        """Test de l'aide des commandes utilisateur"""
        from epicevents import user
        
        runner = CliRunner()
        result = runner.invoke(user, ['--help'])
        
        assert result.exit_code == 0
        assert "Gestion des collaborateurs" in result.output

    def test_client_commands_help(self):
        """Test de l'aide des commandes client"""
        from epicevents import client
        
        runner = CliRunner()
        result = runner.invoke(client, ['--help'])
        
        assert result.exit_code == 0
        assert "Gestion des clients" in result.output

    def test_contract_commands_help(self):
        """Test de l'aide des commandes contrat"""
        from epicevents import contract
        
        runner = CliRunner()
        result = runner.invoke(contract, ['--help'])
        
        assert result.exit_code == 0
        assert "Gestion des contrats" in result.output

    def test_event_commands_help(self):
        """Test de l'aide des commandes événement"""
        from epicevents import event
        
        runner = CliRunner()
        result = runner.invoke(event, ['--help'])
        
        assert result.exit_code == 0
        assert "Gestion des événements" in result.output

    @patch('src.views.auth_view.AuthView.login_command')
    def test_login_command_execution(self, mock_login):
        """Test d'exécution de la commande login"""
        from epicevents import login
        
        runner = CliRunner()
        result = runner.invoke(login, ['--email', 'test@example.com'])
        
        assert result.exit_code == 0
        mock_login.assert_called_once_with('test@example.com')

    @patch('src.views.auth_view.AuthView.logout_command')
    def test_logout_command_execution(self, mock_logout):
        """Test d'exécution de la commande logout"""
        from epicevents import logout
        
        runner = CliRunner()
        result = runner.invoke(logout)
        
        assert result.exit_code == 0
        mock_logout.assert_called_once()

    @patch('src.views.auth_view.AuthView.status_command')
    def test_status_command_execution(self, mock_status):
        """Test d'exécution de la commande status"""
        from epicevents import status
        
        runner = CliRunner()
        result = runner.invoke(status)
        
        assert result.exit_code == 0
        mock_status.assert_called_once()

    @patch('src.views.user_view.UserView.create_user_command')
    def test_user_create_command_execution(self, mock_create):
        """Test d'exécution de la commande user create"""
        from epicevents import user
        
        runner = CliRunner()
        result = runner.invoke(user, ['create'])
        
        assert result.exit_code == 0
        mock_create.assert_called_once()

    @patch('src.views.user_view.UserView.list_users_command')
    def test_user_list_command_execution(self, mock_list):
        """Test d'exécution de la commande user list"""
        from epicevents import user
        
        runner = CliRunner()
        result = runner.invoke(user, ['list'])
        
        assert result.exit_code == 0
        mock_list.assert_called_once()

    @patch('src.views.client_view.ClientView.create_client_command')
    def test_client_create_command_execution(self, mock_create):
        """Test d'exécution de la commande client create"""
        from epicevents import client
        
        runner = CliRunner()
        result = runner.invoke(client, ['create'])
        
        assert result.exit_code == 0
        mock_create.assert_called_once()

    @patch('src.views.contract_view.ContractView.create_contract_command')
    def test_contract_create_command_execution(self, mock_create):
        """Test d'exécution de la commande contract create"""
        from epicevents import contract
        
        runner = CliRunner()
        result = runner.invoke(contract, ['create', '1'])  # Client ID
        
        assert result.exit_code == 0
        mock_create.assert_called_once_with(1)

    @patch('src.views.event_view.EventView.create_event_command')
    def test_event_create_command_execution(self, mock_create):
        """Test d'exécution de la commande event create"""
        from epicevents import event
        
        runner = CliRunner()
        result = runner.invoke(event, ['create', '1'])  # Contract ID
        
        assert result.exit_code == 0
        mock_create.assert_called_once_with(1)

    def test_cli_subcommands_structure(self):
        """Test de la structure des sous-commandes"""
        from epicevents import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        
        # Vérifier que toutes les commandes principales sont présentes
        expected_commands = [
            'init', 'login', 'logout', 'status',
            'user', 'client', 'contract', 'event'
        ]
        
        for command in expected_commands:
            assert command in result.output

    def test_invalid_command(self):
        """Test de commande invalide"""
        from epicevents import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ['invalid-command'])
        
        assert result.exit_code != 0
        assert "No such command" in result.output or "Usage:" in result.output
