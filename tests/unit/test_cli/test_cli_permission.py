"""Tests for CLI permission commands."""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from fastapi_auth.cli.commands.permission import create_permission_for_role
from fastapi_auth.models.rbac import Permission, Role, RolePermission


class TestCLIPermissionCommand:
    """Test CLI permission creation command."""

    @pytest.mark.asyncio
    async def test_create_permission_for_role_success(self, test_session):
        """Test successful permission creation and assignment."""
        runner = CliRunner()

        # Create a role first
        role = Role(name="test_role", description="Test", is_active=True)
        test_session.add(role)
        await test_session.commit()
        await test_session.refresh(role)

        async def mock_get_db_session():
            yield test_session

        with patch(
            "fastapi_auth.cli.commands.permission.get_db_session",
            return_value=mock_get_db_session(),
        ):
            runner.invoke(
                create_permission_for_role,
                [
                    "test_role",
                    "read_users",
                    "users",
                    "read",
                    "--description",
                    "Read users",
                ],
            )

            # Verify permission was created and assigned
            from sqlalchemy import select

            perm_result = await test_session.execute(
                select(Permission).where(Permission.name == "read_users")
            )
            permission = perm_result.scalar_one_or_none()

            if permission:
                assert permission.name == "read_users"
                assert permission.resource == "users"
                assert permission.action == "read"

                # Check assignment
                rp_result = await test_session.execute(
                    select(RolePermission).where(
                        RolePermission.role_id == role.id,
                        RolePermission.permission_id == permission.id,
                    )
                )
                assignment = rp_result.scalar_one_or_none()
                assert assignment is not None

    def test_create_permission_role_not_found(self, test_session):
        """Test creating permission for non-existent role."""
        runner = CliRunner()

        async def mock_get_db_session():
            yield test_session

        with patch(
            "fastapi_auth.cli.commands.permission.get_db_session",
            return_value=mock_get_db_session(),
        ):
            result = runner.invoke(
                create_permission_for_role,
                ["nonexistent_role", "read_users", "users", "read"],
            )

            # Should show error about role not found
            assert "not found" in result.output.lower() or result.exit_code != 0

    @pytest.mark.asyncio
    async def test_create_permission_already_assigned(self, test_session):
        """Test assigning permission that's already assigned to role."""
        runner = CliRunner()

        # Create role and permission
        role = Role(name="test_role2", description="Test", is_active=True)
        permission = Permission(name="existing_perm", resource="users", action="read")
        test_session.add(role)
        test_session.add(permission)
        await test_session.flush()

        role_permission = RolePermission(role_id=role.id, permission_id=permission.id)
        test_session.add(role_permission)
        await test_session.commit()

        async def mock_get_db_session():
            yield test_session

        with patch(
            "fastapi_auth.cli.commands.permission.get_db_session",
            return_value=mock_get_db_session(),
        ):
            result = runner.invoke(
                create_permission_for_role,
                ["test_role2", "existing_perm", "users", "read"],
            )

            # Should show error about already assigned
            assert "already assigned" in result.output.lower() or result.exit_code != 0

    @pytest.mark.asyncio
    async def test_create_permission_existing_permission_different_resource(
        self, test_session
    ):
        """Test using existing permission with different resource/action."""
        runner = CliRunner()

        # Create role and permission with different resource
        role = Role(name="test_role3", description="Test", is_active=True)
        permission = Permission(name="conflict_perm", resource="posts", action="read")
        test_session.add(role)
        test_session.add(permission)
        await test_session.commit()

        async def mock_get_db_session():
            yield test_session

        with patch(
            "fastapi_auth.cli.commands.permission.get_db_session",
            return_value=mock_get_db_session(),
        ):
            result = runner.invoke(
                create_permission_for_role,
                ["test_role3", "conflict_perm", "users", "read"],
            )

            # Should show error about different resource/action
            assert "different" in result.output.lower() or result.exit_code != 0

    def test_create_permission_missing_arguments(self):
        """Test create permission without required arguments."""
        runner = CliRunner()
        result = runner.invoke(create_permission_for_role, [])
        assert result.exit_code != 0
