import click
from rich.console import Console

from cli.commands.permission import create_permission_for_role
from cli.commands.role import create_role
from cli.commands.social import add_social_provider
from cli.commands.user import create_user

console = Console()


@click.group()
def cli():
    """FastAPI Auth CLI - Manage users, roles, permissions, and social providers."""
    pass


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
