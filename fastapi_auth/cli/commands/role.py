import click
from sqlalchemy import select

from fastapi_auth.cli.utils import (
    get_db_session,
    print_error,
    print_table,
    run_async,
)
from fastapi_auth.models.rbac import Role


@click.command("create-role")
@click.argument("name", required=True)
@click.option("--description", help="Role description")
@click.option(
    "--is-active/--no-is-active", default=True, help="Whether the role is active"
)
def create_role(name: str, description: str | None, is_active: bool) -> None:
    """Create a new role."""

    async def _create_role():
        async with get_db_session() as session:
            # Check if role already exists
            result = await session.execute(select(Role).where(Role.name == name))
            existing_role = result.scalar_one_or_none()
            if existing_role:
                print_error(f"Role '{name}' already exists.")
                return

            # Create role
            role = Role(
                name=name,
                description=description,
                is_active=is_active,
            )

            session.add(role)
            await session.commit()
            await session.refresh(role)

            # Display role details in a formatted table
            print_table(
                title="Role Created Successfully",
                rows=[
                    {
                        "Field": "Name",
                        "Value": role.name,
                    },
                    {
                        "Field": "Description",
                        "Value": role.description or "N/A",
                    },
                    {
                        "Field": "ID",
                        "Value": str(role.id),
                    },
                    {
                        "Field": "Is Active",
                        "Value": str(role.is_active),
                    },
                ],
                column_names=["Field", "Value"],
            )

    try:
        run_async(_create_role())
    except Exception as e:
        print_error(f"Failed to create role: {str(e)}")
        raise click.Abort()
