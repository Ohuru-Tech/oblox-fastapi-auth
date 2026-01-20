import click
from rich.console import Console

from fastapi_auth.cli.commands.permission import create_permission_for_role
from fastapi_auth.cli.commands.role import create_role
from fastapi_auth.cli.commands.social import add_social_provider
from fastapi_auth.cli.commands.user import create_user
from fastapi_auth.settings import configure_settings, get_settings

console = Console()


@click.group()
@click.option(
    "--database-url",
    help="Database connection string (e.g., postgresql+asyncpg://user:pass@localhost/db)",
)
@click.option("--jwt-secret-key", help="JWT secret key for token signing")
@click.option("--encryption-key", help="Encryption key for field-level encryption")
@click.option(
    "--email-backend",
    type=click.Choice(["smtp", "azure", "console"], case_sensitive=False),
    help="Email backend to use",
)
@click.option("--timezone", help="Timezone setting (e.g., UTC, America/New_York)")
@click.pass_context
def cli(ctx, database_url, jwt_secret_key, encryption_key, email_backend, timezone):
    """FastAPI Auth CLI - Manage users, roles, permissions, and social providers."""
    # Collect options that were provided
    config_options = {}
    if database_url:
        config_options["database_url"] = database_url
    if jwt_secret_key:
        config_options["jwt_secret_key"] = jwt_secret_key
    if encryption_key:
        config_options["encryption_key"] = encryption_key
    if email_backend:
        config_options["email_backend"] = email_backend.lower()
    if timezone:
        config_options["timezone"] = timezone

    # If any options were provided, configure settings
    if config_options:
        configure_settings(**config_options)
    else:
        # Try to get settings to check if they're already configured
        # If not configured and database_url is required, we'll get an error when commands try to use it
        try:
            get_settings()
            # Settings are already configured, nothing to do
        except Exception:
            # Settings not configured, but we'll let commands handle the error
            # This allows CLI to work if configure_settings() was called elsewhere
            pass

    # Store context for subcommands
    ctx.ensure_object(dict)


# Register commands
cli.add_command(create_user)
cli.add_command(create_role)
cli.add_command(create_permission_for_role)
cli.add_command(add_social_provider)


def main():
    """Main entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
