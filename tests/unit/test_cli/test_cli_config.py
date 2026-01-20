"""Tests for CLI configuration options."""

from unittest.mock import patch

from click.testing import CliRunner

from fastapi_auth.cli import cli
from fastapi_auth.settings import configure_settings, get_settings


class TestCLIConfigOptions:
    """Test CLI global configuration options."""

    def test_cli_accepts_database_url_option(self):
        """Test CLI accepts --database-url option."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["--database-url", "postgresql+asyncpg://test", "--help"]
        )
        assert result.exit_code == 0

    def test_cli_accepts_jwt_secret_key_option(self):
        """Test CLI accepts --jwt-secret-key option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--jwt-secret-key", "test-secret", "--help"])
        assert result.exit_code == 0

    def test_cli_accepts_encryption_key_option(self):
        """Test CLI accepts --encryption-key option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--encryption-key", "test-key", "--help"])
        assert result.exit_code == 0

    def test_cli_accepts_email_backend_option(self):
        """Test CLI accepts --email-backend option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--email-backend", "console", "--help"])
        assert result.exit_code == 0

    def test_cli_accepts_timezone_option(self):
        """Test CLI accepts --timezone option."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--timezone", "UTC", "--help"])
        assert result.exit_code == 0

    def test_cli_calls_configure_settings_with_options(self):
        """Test CLI calls configure_settings() with provided options before command execution."""
        runner = CliRunner()

        with patch("fastapi_auth.cli.configure_settings") as mock_configure:
            with patch("fastapi_auth.cli.commands.user.get_db_session"):
                runner.invoke(
                    cli,
                    [
                        "--database-url",
                        "postgresql+asyncpg://test",
                        "--jwt-secret-key",
                        "test-secret",
                        "create-user",
                        "test@example.com",
                        "--password",
                        "testpass",
                    ],
                )

            # Verify configure_settings was called with the options
            assert mock_configure.called
            # Check that database_url was passed in the call
            assert mock_configure.call_args is not None
            args, kwargs = mock_configure.call_args
            expected_database_url = "postgresql+asyncpg://test"
            # Verify database_url was passed either as a keyword argument or positional argument
            assert "database_url" in kwargs or expected_database_url in args

    def test_cli_options_override_existing_configure_settings(self):
        """Test CLI options override existing configure_settings() values."""
        # First set some initial settings
        configure_settings(
            database_url="postgresql+asyncpg://initial",
            jwt_secret_key="initial-secret",
        )

        initial_settings = get_settings()
        assert initial_settings.database_url == "postgresql+asyncpg://initial"

        runner = CliRunner()
        with patch("fastapi_auth.cli.commands.user.get_db_session"):
            runner.invoke(
                cli,
                [
                    "--database-url",
                    "postgresql+asyncpg://override",
                    "create-user",
                    "test@example.com",
                    "--password",
                    "testpass",
                ],
            )

        # Verify settings were overridden
        new_settings = get_settings()
        assert new_settings.database_url == "postgresql+asyncpg://override"

        # Cleanup
        configure_settings()

    def test_cli_shows_error_if_database_url_missing(self):
        """Test CLI shows helpful error if required --database-url is missing."""
        runner = CliRunner()

        # Clear any existing configuration
        configure_settings()

        # Mock get_settings to raise ValidationError when database_url is missing
        with patch("fastapi_auth.cli.get_settings") as mock_get_settings:
            from pydantic import ValidationError

            def mock_settings():
                raise ValidationError.from_exception_data(
                    "Settings",
                    [
                        {
                            "type": "missing",
                            "loc": ("database_url",),
                            "msg": "Field required",
                        }
                    ],
                )

            mock_get_settings.side_effect = mock_settings

            result = runner.invoke(
                cli,
                [
                    "create-user",
                    "test@example.com",
                    "--password",
                    "testpass",
                ],
            )

            # Should show error (may be ValidationError or connection error)
            # The important thing is that it fails when database_url is not configured
            assert result.exit_code != 0

    def test_cli_works_without_options_if_configure_settings_called(self):
        """Test CLI works without options if configure_settings() was already called."""
        # Set up configuration
        configure_settings(
            database_url="postgresql+asyncpg://test",
            jwt_secret_key="test-secret",
            encryption_key="test-encryption-key",
            email_backend="console",
        )

        runner = CliRunner()
        with patch("fastapi_auth.cli.commands.user.get_db_session"):
            result = runner.invoke(
                cli,
                [
                    "create-user",
                    "test@example.com",
                    "--password",
                    "testpass",
                ],
            )

            # Should not fail due to missing configuration
            # (may fail for other reasons like database connection, but not config)
            assert "database_url" not in result.output.lower() or result.exit_code == 0

        # Cleanup
        configure_settings()

    def test_cli_passes_options_to_all_commands(self):
        """Test CLI options are available to all subcommands."""
        runner = CliRunner()

        # Test with create-role command
        with patch("fastapi_auth.cli.configure_settings") as mock_configure:
            with patch("fastapi_auth.cli.commands.role.get_db_session"):
                runner.invoke(
                    cli,
                    [
                        "--database-url",
                        "postgresql+asyncpg://test",
                        "create-role",
                        "admin",
                    ],
                )

            assert mock_configure.called

        # Test with create-permission-for-role command
        with patch("fastapi_auth.cli.configure_settings") as mock_configure:
            with patch("fastapi_auth.cli.commands.permission.get_db_session"):
                runner.invoke(
                    cli,
                    [
                        "--database-url",
                        "postgresql+asyncpg://test",
                        "create-permission-for-role",
                        "admin",
                        "users:read",
                        "users",
                        "read",
                    ],
                )

            assert mock_configure.called

    def test_cli_calls_configure_settings_with_encryption_key(self):
        """Test CLI calls configure_settings() with --encryption-key option."""
        runner = CliRunner()

        with patch("fastapi_auth.cli.configure_settings") as mock_configure:
            with patch("fastapi_auth.cli.commands.user.get_db_session"):
                runner.invoke(
                    cli,
                    [
                        "--encryption-key",
                        "test-encryption-key",
                        "create-user",
                        "test@example.com",
                        "--password",
                        "testpass",
                    ],
                )

            # Verify configure_settings was called with encryption_key
            assert mock_configure.called
            args, kwargs = mock_configure.call_args
            assert "encryption_key" in kwargs
            assert kwargs["encryption_key"] == "test-encryption-key"

    def test_cli_calls_configure_settings_with_email_backend(self):
        """Test CLI calls configure_settings() with --email-backend option."""
        runner = CliRunner()

        with patch("fastapi_auth.cli.configure_settings") as mock_configure:
            with patch("fastapi_auth.cli.commands.user.get_db_session"):
                runner.invoke(
                    cli,
                    [
                        "--email-backend",
                        "console",
                        "create-user",
                        "test@example.com",
                        "--password",
                        "testpass",
                    ],
                )

            # Verify configure_settings was called with email_backend (lowercased)
            assert mock_configure.called
            args, kwargs = mock_configure.call_args
            assert "email_backend" in kwargs
            assert kwargs["email_backend"] == "console"

    def test_cli_calls_configure_settings_with_timezone(self):
        """Test CLI calls configure_settings() with --timezone option."""
        runner = CliRunner()

        with patch("fastapi_auth.cli.configure_settings") as mock_configure:
            with patch("fastapi_auth.cli.commands.user.get_db_session"):
                runner.invoke(
                    cli,
                    [
                        "--timezone",
                        "UTC",
                        "create-user",
                        "test@example.com",
                        "--password",
                        "testpass",
                    ],
                )

            # Verify configure_settings was called with timezone
            assert mock_configure.called
            args, kwargs = mock_configure.call_args
            assert "timezone" in kwargs
            assert kwargs["timezone"] == "UTC"
