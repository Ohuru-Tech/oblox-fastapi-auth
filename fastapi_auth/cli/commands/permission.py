import click
from sqlalchemy import select

from fastapi_auth.cli.utils import get_db_session, print_error, print_success, run_async
from fastapi_auth.models.rbac import Permission, Role, RolePermission


@click.command("create-permission-for-role")
@click.argument("role_name", required=True)
@click.argument("permission_name", required=True)
@click.argument("resource", required=True)
@click.argument("action", required=True)
@click.option("--description", help="Permission description")
def create_permission_for_role(
    role_name: str,
    permission_name: str,
    resource: str,
    action: str,
    description: str | None,
) -> None:
    """Create a permission and assign it to a role. If permission already exists, assign it to the role."""

    async def _create_permission_for_role():
        async with get_db_session() as session:
            # Check if role exists
            role_result = await session.execute(
                select(Role).where(Role.name == role_name)
            )
            role = role_result.scalar_one_or_none()
            if not role:
                print_error(f"Role '{role_name}' not found.")
                return

            # Check if permission exists
            perm_result = await session.execute(
                select(Permission).where(Permission.name == permission_name)
            )
            permission = perm_result.scalar_one_or_none()

            if permission:
                # Permission exists, verify it matches the provided resource/action
                if permission.resource != resource or permission.action != action:
                    print_error(
                        f"Permission '{permission_name}' exists but with different "
                        f"resource/action (current: {permission.resource}/{permission.action}, "
                        f"provided: {resource}/{action})."
                    )
                    return
                print_success(f"Using existing permission '{permission_name}'")
            else:
                # Create new permission
                permission = Permission(
                    name=permission_name,
                    resource=resource,
                    action=action,
                    description=description,
                )
                session.add(permission)
                await session.flush()  # Flush to get the ID
                print_success(f"Created new permission '{permission_name}'")

            # Check if permission is already assigned to role
            existing_assignment = await session.execute(
                select(RolePermission).where(
                    RolePermission.role_id == role.id,
                    RolePermission.permission_id == permission.id,
                )
            )
            if existing_assignment.scalar_one_or_none():
                print_error(
                    f"Permission '{permission_name}' is already assigned to role '{role_name}'."
                )
                return

            # Assign permission to role
            role_permission = RolePermission(
                role_id=role.id, permission_id=permission.id
            )
            session.add(role_permission)
            await session.commit()

            print_success(
                f"Permission '{permission_name}' assigned to role '{role_name}'"
            )
            print_success(
                f"  Permission: {permission.name} ({permission.resource}/{permission.action})"
            )
            print_success(f"  Role: {role.name}")

    try:
        run_async(_create_permission_for_role())
    except Exception as e:
        print_error(f"Failed to create/assign permission: {str(e)}")
        raise click.Abort()
