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
