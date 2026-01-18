import pytest

from fastapi_auth.models.rbac import Permission, Role, RolePermission, UserRole
from fastapi_auth.repositories.rbac_repository import RBACRepository


class TestRBACRepositoryGetRoleByName:
    """Test RBACRepository get_role_by_name method."""

    @pytest.mark.asyncio
    async def test_get_role_by_name_finds_existing_role(self, db_session):
        """Test that get_role_by_name finds an existing role."""
        repository = RBACRepository(db_session)

        # Create a role
        role = Role(name="test_role", description="Test role description")
        db_session.add(role)
        await db_session.commit()
        await db_session.refresh(role)

        found_role = await repository.get_role_by_name(name="test_role")

        assert found_role is not None
        assert found_role.name == "test_role"
        assert found_role.id == role.id

    @pytest.mark.asyncio
    async def test_get_role_by_name_returns_none_for_nonexistent_role(self, db_session):
        """Test that get_role_by_name returns None for non-existent role."""
        repository = RBACRepository(db_session)

        found_role = await repository.get_role_by_name(name="nonexistent_role")

        assert found_role is None


class TestRBACRepositoryGetRolesByUserId:
    """Test RBACRepository get_roles_by_user_id method."""

    @pytest.mark.asyncio
    async def test_get_roles_by_user_id_with_user_having_roles(
        self, db_session, test_user
    ):
        """Test get_roles_by_user_id returns roles for user with roles."""
        repository = RBACRepository(db_session)

        # Create roles
        role1 = Role(name="editor", description="Editor role")
        role2 = Role(name="viewer", description="Viewer role")
        db_session.add(role1)
        db_session.add(role2)
        await db_session.commit()
        await db_session.refresh(role1)
        await db_session.refresh(role2)

        # Assign roles to user - id will be auto-generated
        user_role1 = UserRole(user_id=test_user.id, role_id=role1.id)
        user_role2 = UserRole(user_id=test_user.id, role_id=role2.id)
        db_session.add(user_role1)
        db_session.add(user_role2)
        await db_session.commit()

        roles = await repository.get_roles_by_user_id(user_id=test_user.id)

        assert len(roles) == 2
        role_names = {role.name for role in roles}
        assert "editor" in role_names
        assert "viewer" in role_names

    @pytest.mark.asyncio
    async def test_get_roles_by_user_id_with_user_having_no_roles(
        self, db_session, test_user
    ):
        """Test get_roles_by_user_id returns empty list for user with no roles."""
        repository = RBACRepository(db_session)

        roles = await repository.get_roles_by_user_id(user_id=test_user.id)

        assert roles == []


class TestRBACRepositoryGetPermissionsByUserId:
    """Test RBACRepository get_permissions_by_user_id method."""

    @pytest.mark.asyncio
    async def test_get_permissions_by_user_id(self, db_session, test_user):
        """Test get_permissions_by_user_id returns permissions for user."""
        repository = RBACRepository(db_session)

        # Create role and permission
        role = Role(name="editor", description="Editor role")
        permission = Permission(
            name="read:users", resource="users", action="read", description="Read users"
        )
        db_session.add(role)
        db_session.add(permission)
        await db_session.commit()
        await db_session.refresh(role)
        await db_session.refresh(permission)

        # Assign role to user
        user_role = UserRole(user_id=test_user.id, role_id=role.id)
        db_session.add(user_role)

        # Assign permission to role - id will be auto-generated
        role_permission = RolePermission(role_id=role.id, permission_id=permission.id)
        db_session.add(role_permission)
        await db_session.commit()

        permissions = await repository.get_permissions_by_user_id(user_id=test_user.id)

        assert len(permissions) == 1
        assert permissions[0].name == "read:users"

    @pytest.mark.asyncio
    async def test_get_permissions_by_user_id_with_no_permissions(
        self, db_session, test_user
    ):
        """Test get_permissions_by_user_id returns empty list when user has no permissions."""
        repository = RBACRepository(db_session)

        permissions = await repository.get_permissions_by_user_id(user_id=test_user.id)

        assert permissions == []


class TestRBACRepositoryGetPermissionsByRoleId:
    """Test RBACRepository get_permissions_by_role_id method."""

    @pytest.mark.asyncio
    async def test_get_permissions_by_role_id(self, db_session):
        """Test get_permissions_by_role_id returns permissions for role."""
        repository = RBACRepository(db_session)

        # Create role and permissions
        role = Role(name="admin", description="Admin role")
        perm1 = Permission(
            name="read:users", resource="users", action="read", description="Read users"
        )
        perm2 = Permission(
            name="write:users",
            resource="users",
            action="write",
            description="Write users",
        )
        db_session.add(role)
        db_session.add(perm1)
        db_session.add(perm2)
        await db_session.commit()
        await db_session.refresh(role)
        await db_session.refresh(perm1)
        await db_session.refresh(perm2)

        # Assign permissions to role - id will be auto-generated
        role_perm1 = RolePermission(role_id=role.id, permission_id=perm1.id)
        role_perm2 = RolePermission(role_id=role.id, permission_id=perm2.id)
        db_session.add(role_perm1)
        db_session.add(role_perm2)
        await db_session.commit()

        permissions = await repository.get_permissions_by_role_id(role_id=role.id)

        assert len(permissions) == 2
        permission_names = {perm.name for perm in permissions}
        assert "read:users" in permission_names
        assert "write:users" in permission_names

    @pytest.mark.asyncio
    async def test_get_permissions_by_role_id_with_no_permissions(self, db_session):
        """Test get_permissions_by_role_id returns empty list when role has no permissions."""
        repository = RBACRepository(db_session)

        # Create role without permissions
        role = Role(name="viewer", description="Viewer role")
        db_session.add(role)
        await db_session.commit()
        await db_session.refresh(role)

        permissions = await repository.get_permissions_by_role_id(role_id=role.id)

        assert permissions == []
