import click
from sqlalchemy import select

from fastapi_auth.cli.utils import (
    get_db_session,
    print_error,
    print_table,
    run_async,
)
from fastapi_auth.models.user import User
from fastapi_auth.schemas.user import UserSignupSchema
from fastapi_auth.utils.password import hash_password


@click.command("create-user")
@click.argument("email", required=True)
@click.option("--name", help="User's full name")
@click.option("--password", help="User's password (will prompt if not provided)")
@click.option("--is-staff", is_flag=True, default=False, help="Mark user as staff")
def create_user(
    email: str, name: str | None, password: str | None, is_staff: bool
) -> None:
    """Create a new user."""

    async def _create_user():
        async with get_db_session() as session:
            # Check if user already exists
            result = await session.execute(select(User).where(User.email == email))
            existing_user = result.scalar_one_or_none()
            if existing_user:
                print_error(f"User with email {email} already exists.")
                return

            # Prompt for password if not provided
            if not password:
                password_value = click.prompt(
                    "Password", hide_input=True, confirmation_prompt=True
                )
            else:
                password_value = password

            # Hash password (bcrypt.hashpw returns bytes, decode to string for storage)
            hashed_password_bytes = hash_password(password_value)
            # Handle both bytes and str return types (type hint says str but bcrypt returns bytes)
            if isinstance(hashed_password_bytes, bytes):
                hashed_password = hashed_password_bytes.decode("utf-8")
            else:
                hashed_password = hashed_password_bytes

            # Create user schema
            user_data = UserSignupSchema(
                email=email,
                name=name,
                password=hashed_password,
                profile_pic=None,
            )

            # Create user
            user = User(
                email=user_data.email,
                name=user_data.name,
                password=user_data.password,
                profile_pic=user_data.profile_pic,
                is_staff=is_staff,
            )

            session.add(user)
            await session.commit()
            await session.refresh(user)

            # Display user details in a formatted table
            print_table(
                title="User Created Successfully",
                rows=[
                    {
                        "Field": "Email",
                        "Value": user.email,
                    },
                    {
                        "Field": "Name",
                        "Value": user.name or "N/A",
                    },
                    {
                        "Field": "ID",
                        "Value": str(user.id),
                    },
                    {
                        "Field": "Is Staff",
                        "Value": str(user.is_staff),
                    },
                ],
                column_names=["Field", "Value"],
            )

    try:
        run_async(_create_user())
    except Exception as e:
        print_error(f"Failed to create user: {str(e)}")
        raise click.Abort()
