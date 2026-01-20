import click
from sqlalchemy import select

from fastapi_auth.cli.utils import (
    get_db_session,
    print_error,
    print_table,
    run_async,
)
from fastapi_auth.models.social_providers import SocialProvider, SupportedProviders


@click.command("add-social-provider")
@click.argument(
    "provider_type",
    type=click.Choice([p.value for p in SupportedProviders], case_sensitive=False),
)
@click.option("--client-id", help="OAuth client ID (will prompt if not provided)")
@click.option(
    "--client-secret", help="OAuth client secret (will prompt if not provided)"
)
def add_social_provider(
    provider_type: str, client_id: str | None, client_secret: str | None
) -> None:
    """Add a social authentication provider."""

    async def _add_social_provider():
        async with get_db_session() as session:
            # Convert string to enum
            provider_enum = SupportedProviders(provider_type.lower())

            # Check if provider already exists
            result = await session.execute(
                select(SocialProvider).where(
                    SocialProvider.provider_type == provider_enum.value
                )
            )
            existing_provider = result.scalar_one_or_none()
            if existing_provider:
                print_error(f"Social provider '{provider_type}' already exists.")
                return

            # Prompt for client_id if not provided
            if not client_id:
                client_id_value = click.prompt("Client ID")
            else:
                client_id_value = client_id

            # Prompt for client_secret if not provided
            if not client_secret:
                client_secret_value = click.prompt(
                    "Client Secret", hide_input=True, confirmation_prompt=True
                )
            else:
                client_secret_value = client_secret

            # Create social provider (client_secret will be auto-encrypted via EncryptedString)
            social_provider = SocialProvider(
                provider_type=provider_enum.value,
                client_id=client_id_value,
                client_secret=client_secret_value,
            )

            session.add(social_provider)
            await session.commit()
            await session.refresh(social_provider)

            # Display social provider details in a formatted table
            print_table(
                title="Social Provider Added Successfully",
                rows=[
                    {
                        "Field": "Provider Type",
                        "Value": social_provider.provider_type,
                    },
                    {
                        "Field": "Client ID",
                        "Value": social_provider.client_id,
                    },
                    {
                        "Field": "ID",
                        "Value": str(social_provider.id),
                    },
                ],
                column_names=["Field", "Value"],
            )

    try:
        run_async(_add_social_provider())
    except Exception as e:
        print_error(f"Failed to add social provider: {str(e)}")
        raise click.Abort()
