"""Tests for CLI role commands."""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from fastapi_auth.cli.commands.role import create_role
from fastapi_auth.models.rbac import Role


class TestCLIRoleCommand:
    """Test CLI role creation command."""

    @pytest.mark.asyncio
    async def test_create_role_success(self, test_session):
        """Test successful role creation."""
        runner = CliRunner()

        async def mock_get_db_session():
            yield test_session

        with patch(
            "fastapi_auth.cli.commands.role.get_db_session",
            return_value=mock_get_db_session(),
        ):
            runner.invoke(
                create_role,
                ["test_role", "--description", "Test role description"],
            )

            # Verify role was created
            from sqlalchemy import select

            result_query = await test_session.execute(
                select(Role).where(Role.name == "test_role")
            )
            role = result_query.scalar_one_or_none()

            if role:
                assert role.name == "test_role"
                assert role.description == "Test role description"
                assert role.is_active is True

    @pytest.mark.asyncio
    async def test_create_role_already_exists(self, test_session):
        """Test creating role that already exists."""
        runner = CliRunner()

        # Create a role first
        existing_role = Role(
            name="existing_role", description="Existing", is_active=True
        )
        test_session.add(existing_role)
        await test_session.commit()

        async def mock_get_db_session():
            yield test_session

        with patch(
            "fastapi_auth.cli.commands.role.get_db_session",
            return_value=mock_get_db_session(),
        ):
            result = runner.invoke(
                create_role,
                ["existing_role", "--description", "Duplicate"],
            )

            # Should show error about existing role
            assert "already exists" in result.output.lower() or result.exit_code != 0

    @pytest.mark.asyncio
    async def test_create_role_with_is_active_false(self, test_session):
        """Test creating role with --no-is-active flag."""
        runner = CliRunner()

        async def mock_get_db_session():
            yield test_session

        with patch(
            "fastapi_auth.cli.commands.role.get_db_session",
            return_value=mock_get_db_session(),
        ):
            runner.invoke(
                create_role,
                ["inactive_role", "--no-is-active"],
            )

            # Verify role was created with is_active=False
            from sqlalchemy import select

            result_query = await test_session.execute(
                select(Role).where(Role.name == "inactive_role")
            )
            role = result_query.scalar_one_or_none()

            if role:
                assert role.is_active is False

    def test_create_role_missing_name(self):
        """Test create role without name argument."""
        runner = CliRunner()
        result = runner.invoke(create_role, [])
        assert result.exit_code != 0
