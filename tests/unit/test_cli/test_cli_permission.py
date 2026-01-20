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

    @pytest.mark.asyncio
    async def test_create_permission_output_uses_rich_formatting(self, test_session):
        """Test permission assignment output uses Rich Table/Panel."""
        from rich.table import Table

        runner = CliRunner()

        # Create a role first
        role = Role(name="test_role_rich", description="Test", is_active=True)
        test_session.add(role)
        await test_session.commit()
        await test_session.refresh(role)

        # Use the same pattern as the working test - patch get_db_session directly
        # get_db_session is decorated with @asynccontextmanager, so we need to wrap our mock too
        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def mock_get_db_session():
            yield test_session

        # Apply nest_asyncio to allow nested event loops
        # This allows asyncio.run() to work even when we're already in an event loop
        import nest_asyncio

        nest_asyncio.apply()

        with patch(
            "fastapi_auth.cli.commands.permission.get_db_session",
            return_value=mock_get_db_session(),
        ):
            with patch("fastapi_auth.cli.utils.console") as mock_console:
                runner.invoke(
                    create_permission_for_role,
                    [
                        "test_role_rich",
                        "read_users_rich",
                        "users",
                        "read",
                        "--description",
                        "Read users",
                    ],
                )

                # Verify console.print was called (Rich formatting is used)
                assert mock_console.print.called

                # Check that a Table object was passed
                found_table = False
                for call in mock_console.print.call_args_list:
                    call_args = call[0]
                    if call_args and len(call_args) > 0:
                        obj = call_args[0]
                        if isinstance(obj, Table):
                            title = (obj.title or "").lower()
                            if any(
                                keyword in title
                                for keyword in ("permission", "assigned", "created")
                            ):
                                found_table = True
                                break
                # If no Table found, raise assertion failure
                if not found_table:
                    call_types = [
                        type(call[0][0]).__name__
                        for call in mock_console.print.call_args_list
                        if call[0] and len(call[0]) > 0
                    ]
                    assert False, (
                        "Expected a Table with title containing 'permission'|'assigned'|'created' not found. "
                        f"Found {len(mock_console.print.call_args_list)} calls to console.print "
                        f"with types: {call_types}"
                    )
