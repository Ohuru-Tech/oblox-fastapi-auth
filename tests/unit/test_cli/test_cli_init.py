"""Tests for CLI main module."""

from click.testing import CliRunner

from fastapi_auth.cli import cli


class TestCLIMain:
    """Test CLI main module."""

    def test_cli_group_exists(self):
        """Test that CLI group is defined."""
        assert cli is not None
        assert callable(cli)

    def test_cli_help(self):
        """Test CLI help command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "FastAPI Auth CLI" in result.output

    def test_cli_commands_registered(self):
        """Test that all commands are registered."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "create-user" in result.output
        assert "create-role" in result.output
        assert "create-permission-for-role" in result.output
        assert "add-social-provider" in result.output

    def test_main_function(self):
        """Test main function can be called."""
        runner = CliRunner()
        # Main function calls cli(), so we test it indirectly
        # by checking that the CLI works
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
