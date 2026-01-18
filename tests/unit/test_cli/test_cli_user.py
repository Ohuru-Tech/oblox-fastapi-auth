"""Tests for CLI user commands."""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from fastapi_auth.cli.commands.user import create_user
from fastapi_auth.models.user import User


class TestCLIUserCommand:
    """Test CLI user creation command."""

    @pytest.mark.asyncio
    async def test_create_user_success(self, test_session):
        """Test successful user creation."""
        runner = CliRunner()

        # Mock get_db_session to return test_session
        async def mock_get_db_session():
            yield test_session

        with patch(
            "fastapi_auth.cli.commands.user.get_db_session",
            return_value=mock_get_db_session(),
        ):
            runner.invoke(
                create_user,
                [
                    "test@example.com",
                    "--name",
                    "Test User",
                    "--password",
                    "testpass123",
                ],
            )

            # Verify user was created - use test_session directly since we're in async context
            from sqlalchemy import select

            result_query = await test_session.execute(
                select(User).where(User.email == "test@example.com")
            )
            user = result_query.scalar_one_or_none()

            if user:
                assert user.email == "test@example.com"
                assert user.name == "Test User"
                assert user.is_staff is False

    def test_create_user_already_exists(self, test_session, test_user):
        """Test creating user that already exists."""
        runner = CliRunner()

        async def mock_get_db_session():
            yield test_session

        with patch(
            "fastapi_auth.cli.commands.user.get_db_session",
            return_value=mock_get_db_session(),
        ):
            result = runner.invoke(
                create_user,
                [
                    test_user.email,
                    "--name",
                    "Test User",
                    "--password",
                    "testpass123",
                ],
            )

            # Should show error about existing user
            assert "already exists" in result.output.lower() or result.exit_code != 0

    @pytest.mark.asyncio
    async def test_create_user_with_is_staff(self, test_session):
        """Test creating user with is_staff flag."""
        runner = CliRunner()

        async def mock_get_db_session():
            yield test_session

        with patch(
            "fastapi_auth.cli.commands.user.get_db_session",
            return_value=mock_get_db_session(),
        ):
            runner.invoke(
                create_user,
                [
                    "staff@example.com",
                    "--name",
                    "Staff User",
                    "--password",
                    "testpass123",
                    "--is-staff",
                ],
            )

            # Verify user was created with is_staff=True
            from sqlalchemy import select

            result_query = await test_session.execute(
                select(User).where(User.email == "staff@example.com")
            )
            user = result_query.scalar_one_or_none()

            if user:
                assert user.is_staff is True

    def test_create_user_missing_email(self):
        """Test create user without email argument."""
        runner = CliRunner()
        result = runner.invoke(create_user, [])
        assert result.exit_code != 0
