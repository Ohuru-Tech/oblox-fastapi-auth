import asyncio
from logging.config import fileConfig

from alembic import context
from alembic.autogenerate.render import _repr_type
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.types import TypeDecorator

# Import models module to ensure all model tables are registered in Base.metadata
# In SQLAlchemy's declarative system, tables are registered only when their
# defining classes are imported. Without this import, Base.metadata remains empty.
import fastapi_auth.models  # noqa: F401  # ensure model tables are registered
from fastapi_auth.models.base import Base

# IMPORTANT: Configure settings programmatically BEFORE importing models
# This ensures proper initialization of settings-dependent components
from fastapi_auth.settings import get_settings

# Import Base model for this package's metadata


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# Configure metadata for Alembic autogenerate support
#
# For projects using this package, you should merge metadata from both
# your application and fastapi_auth:
#
#   from fastapi_auth.models import get_metadata as get_auth_metadata
#   from myapp.models import Base as MyAppBase
#
#   # Merge metadata - Alembic will track tables from both sources
#   target_metadata = [MyAppBase.metadata, get_auth_metadata()]
#
# This ensures Alembic can detect changes in both your models and
# fastapi_auth models. Always configure settings programmatically before
# importing models (see configure_settings() call above).
#
# For this package's own migrations, we only use Base.metadata:
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def render_item_func(type_, object_, autogen_context):
    """
    Custom render function for Alembic autogenerate.

    Handles TypeDecorator instances by rendering their underlying SQL type
    instead of the TypeDecorator class itself. This ensures migrations use
    the correct database type (e.g., String) while preserving runtime
    functionality (e.g., encryption/decryption).
    """
    # Only handle "type" items - render_item is called for many different item types
    if type_ == "type" and isinstance(object_, TypeDecorator):
        # Render the underlying SQL type instead of the TypeDecorator
        return _repr_type(object_.impl, autogen_context)

    # Return False to use default rendering for other items
    return False


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    settings = get_settings()
    url = settings.database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_item=render_item_func,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_item=render_item_func,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    settings = get_settings()
    connectable = create_async_engine(settings.database_url)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
