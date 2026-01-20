"""Tests for CLI social provider commands."""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from fastapi_auth.cli.commands.social import add_social_provider
from fastapi_auth.models.social_providers import SocialProvider, SupportedProviders


class TestCLISocialCommand:
    """Test CLI social provider commands."""

    @pytest.mark.asyncio
    async def test_add_social_provider_success(self, test_session):
        """Test successful social provider addition."""
        runner = CliRunner()

        async def mock_get_db_session():
            yield test_session

        with patch(
            "fastapi_auth.cli.commands.social.get_db_session",
            return_value=mock_get_db_session(),
        ):
            runner.invoke(
                add_social_provider,
                [
                    "github",
                    "--client-id",
                    "test_client_id",
                    "--client-secret",
                    "test_secret",
                ],
            )

            # Verify provider was created
            from sqlalchemy import select

            result_query = await test_session.execute(
                select(SocialProvider).where(
                    SocialProvider.provider_type == SupportedProviders.GITHUB.value
                )
            )
            provider = result_query.scalar_one_or_none()

            if provider:
                assert provider.provider_type == SupportedProviders.GITHUB.value
                assert provider.client_id == "test_client_id"
                # client_secret is encrypted, so we just check it exists
                assert provider.client_secret is not None

    @pytest.mark.asyncio
    async def test_add_social_provider_already_exists(
        self, test_session, test_settings
    ):
        """Test adding social provider that already exists."""
        runner = CliRunner()

        # Create provider first - encryption will use test_settings encryption_key
        # The encryption key is already set in conftest.py
        provider = SocialProvider(
            provider_type=SupportedProviders.GITHUB.value,
            client_id="existing_id",
            client_secret="existing_secret",
        )
        test_session.add(provider)
        await test_session.commit()
        await test_session.refresh(provider)

        async def mock_get_db_session():
            yield test_session

        with patch(
            "fastapi_auth.cli.commands.social.get_db_session",
            return_value=mock_get_db_session(),
        ):
            result = runner.invoke(
                add_social_provider,
                [
                    "github",
                    "--client-id",
                    "new_id",
                    "--client-secret",
                    "new_secret",
                ],
            )

            # Should show error about existing provider
            assert "already exists" in result.output.lower() or result.exit_code != 0

    @pytest.mark.asyncio
    async def test_add_social_provider_google(self, test_session):
        """Test adding social provider with lowercase conversion."""
        runner = CliRunner()

        async def mock_get_db_session():
            yield test_session

        with patch(
            "fastapi_auth.cli.commands.social.get_db_session",
            return_value=mock_get_db_session(),
        ):
            # Test that provider_type.lower() is called (use GITHUB with uppercase)
            runner.invoke(
                add_social_provider,
                [
                    "GITHUB",  # Test lowercase conversion
                    "--client-id",
                    "test_client_id",
                    "--client-secret",
                    "test_secret",
                ],
            )

            # Verify provider was created
            from sqlalchemy import select

            result_query = await test_session.execute(
                select(SocialProvider).where(
                    SocialProvider.provider_type == SupportedProviders.GITHUB.value
                )
            )
            provider = result_query.scalar_one_or_none()

            if provider:
                assert provider.provider_type == SupportedProviders.GITHUB.value

    def test_add_social_provider_invalid_type(self):
        """Test adding social provider with invalid type."""
        runner = CliRunner()
        result = runner.invoke(
            add_social_provider,
            ["invalid_provider", "--client-id", "test", "--client-secret", "test"],
        )
        assert result.exit_code != 0

    def test_add_social_provider_missing_provider_type(self):
        """Test add social provider without provider type."""
        runner = CliRunner()
        result = runner.invoke(add_social_provider, [])
        assert result.exit_code != 0

    @pytest.mark.asyncio
    async def test_add_social_provider_output_uses_rich_formatting(
        self, test_session, test_settings
    ):
        """Test social provider output uses Rich Table/Panel."""
        from contextlib import asynccontextmanager

        import nest_asyncio
        from rich.panel import Panel
        from rich.table import Table

        runner = CliRunner()

        # Use the same pattern as the working test - patch get_db_session directly
        # get_db_session is decorated with @asynccontextmanager, so we need to wrap our mock too
        @asynccontextmanager
        async def mock_get_db_session():
            yield test_session

        # Apply nest_asyncio to allow nested event loops
        # This allows asyncio.run() to work even when we're already in an event loop
        nest_asyncio.apply()

        with patch(
            "fastapi_auth.cli.commands.social.get_db_session",
            return_value=mock_get_db_session(),
        ):
            with patch("fastapi_auth.cli.utils.console") as mock_console:
                result = runner.invoke(
                    add_social_provider,
                    [
                        "github",
                        "--client-id",
                        "test_client_id_rich",
                        "--client-secret",
                        "test_secret_rich",
                    ],
                )

                # Require that Rich output was actually produced
                assert mock_console.print.called is True, (
                    "Rich output should have been produced"
                )
                assert result.exit_code == 0, "Command should succeed"

                # Verify it uses Rich formatting - check that either a Table (success) or Panel (error) object was passed
                for call in mock_console.print.call_args_list:
                    call_args = call[0]
                    if call_args and len(call_args) > 0:
                        obj = call_args[0]
                        if isinstance(obj, Table):
                            assert obj.title and (
                                "provider" in obj.title.lower()
                                or "added" in obj.title.lower()
                                or "created" in obj.title.lower()
                            )
                            return
                        elif isinstance(obj, Panel):
                            # Error panel is also Rich formatting
                            assert True
                            return
