# FastAPI Auth

[![CI](https://github.com/Ohuru-Tech/fastapi-auth/actions/workflows/publish.yml/badge.svg)](https://github.com/Ohuru-Tech/fastapi-auth/actions/workflows/publish.yml)
[![PyPI version](https://img.shields.io/pypi/v/oblox-fastapi-auth.svg)](https://pypi.org/project/oblox-fastapi-auth/)
[![codecov](https://codecov.io/gh/Ohuru-Tech/oblox-fastapi-auth/graph/badge.svg?token=5RI47F0DO6)](https://codecov.io/gh/Ohuru-Tech/oblox-fastapi-auth)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive authentication package for FastAPI applications with JWT, RBAC, and social authentication support.

## Features

- ✅ User registration and authentication
- ✅ JWT token management (access & refresh tokens)
- ✅ Role-based access control (RBAC)
- ✅ Social media authentication (GitHub, Google)
- ✅ Password hashing and verification
- ✅ Email verification support
- ✅ Field-level encryption for sensitive data
- ✅ Async/await support throughout
- ✅ Multiple database backends (PostgreSQL, MySQL)
- ✅ Multiple email backends (SMTP, Azure, Console)
- ✅ CLI tools for user and role management

## Installation

Install the package using `uv`:

```bash
uv add oblox-fastapi-auth
```

Or using `pip`:

```bash
pip install oblox-fastapi-auth
```

## Quick Start

### 1. Install and Configure

```bash
# Install the package
uv add oblox-fastapi-auth
```

**Important:** This package requires programmatic configuration. You must call `configure_settings()` before importing any modules that use settings.

```python
# Configure settings BEFORE any other imports
from fastapi_auth import configure_settings

# Configure settings programmatically (recommended)
configure_settings(
    database_url="postgresql+asyncpg://user:password@localhost/dbname",
    jwt_secret_key="your-secret-key-here",
    encryption_key="your-encryption-key-here",  # Generate with: Fernet.generate_key().decode()
    email_backend="console",
    timezone="UTC",
)
```

> **Note:** While environment variables are supported as a fallback, programmatic configuration is strongly recommended for better control and explicit initialization. Environment variables use the `AUTH_` prefix (e.g., `AUTH_DATABASE_URL`).

### 2. Create Your FastAPI Application

```python
# IMPORTANT: Configure settings BEFORE importing other fastapi_auth modules
from fastapi_auth import configure_settings

configure_settings(
    database_url="postgresql+asyncpg://user:password@localhost/dbname",
    jwt_secret_key="your-secret-key-here",
    encryption_key="your-encryption-key-here",
    email_backend="console",
    timezone="UTC",
)

# Now import other modules
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi_auth import auth_router, get_engine
from fastapi_auth.utils.logging import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    try:
        yield
    finally:
        await get_engine().dispose()


app = FastAPI(lifespan=lifespan, title="My FastAPI App")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication routes
app.include_router(auth_router)
```

### 3. Configure Database Migrations with Alembic

When using this package in your application, you need to merge the package's metadata with your own application's metadata so Alembic can track both sets of tables.

#### Step 1: Configure Settings in `migrations/env.py`

**Important:** You must configure settings programmatically in your `migrations/env.py` file before importing any models.

```python
# migrations/env.py
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

# Configure settings BEFORE importing models
from fastapi_auth import configure_settings

configure_settings(
    database_url="postgresql+asyncpg://user:password@localhost/dbname",
    jwt_secret_key="your-secret-key",
    encryption_key="your-encryption-key",
    email_backend="console",
    timezone="UTC",
)

# Now import metadata from both your app and fastapi_auth
from fastapi_auth.models import get_metadata as get_auth_metadata
from myapp.models import Base as MyAppBase  # Your application's Base

# Merge metadata for Alembic
# Alembic will track tables from both your app and fastapi_auth
target_metadata = [MyAppBase.metadata, get_auth_metadata()]

# Rest of your Alembic configuration...
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ... (rest of your env.py configuration)
```

#### Step 2: Create and Run Migrations

```bash
# Initialize Alembic (if not already done)
alembic init migrations

# Create initial migration (will include both your tables and fastapi_auth tables)
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

**Note:** The merged metadata ensures Alembic can detect changes in both your application's models and the fastapi_auth package's models. Always configure settings programmatically in your `migrations/env.py` to ensure proper initialization.

### 4. Use the CLI Tools

```bash
# Create a user
oblox-fastapi-auth-cli create-user user@example.com --name "John Doe" --password "securepassword"

# Create a role
oblox-fastapi-auth-cli create-role admin --description "Administrator role"

# Assign permission to role
oblox-fastapi-auth-cli create-permission-for-role admin users:read users read "Read users"

# Add social provider
oblox-fastapi-auth-cli add-social-provider github --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET
```

## Usage Examples

### Basic Authentication

```python
from fastapi import FastAPI, Depends
from fastapi_auth import auth_router, get_session
from fastapi_auth.services.rbac import required_admin, required_role
from fastapi_auth.models.user import User

app = FastAPI()
app.include_router(auth_router)


@app.get("/protected")
async def protected_route(current_user: User = Depends(required_admin)):
    """Protected route that requires admin role."""
    return {"message": f"Hello, {current_user.email}!"}


@app.get("/user-profile")
async def user_profile(current_user: User = Depends(required_role("user"))):
    """Route that requires 'user' role."""
    return {"email": current_user.email, "name": current_user.name}
```

### Using RBAC Permissions

```python
from fastapi import FastAPI, Depends
from fastapi_auth import auth_router
from fastapi_auth.services.rbac import required_permissions
from fastapi_auth.models.user import User

app = FastAPI()
app.include_router(auth_router)


@app.get("/users")
async def list_users(
    current_user: User = Depends(required_permissions(["users:read"]))
):
    """List users - requires 'users:read' permission."""
    # Your logic here
    return {"users": []}
```

### Programmatic Configuration (Recommended)

**Programmatic configuration is the recommended approach** as it provides explicit control over initialization and ensures settings are configured before any modules that depend on them are imported.

```python
from fastapi_auth import configure_settings, get_settings

# Configure settings programmatically (call this BEFORE importing other fastapi_auth modules)
configure_settings(
    database_url="postgresql+asyncpg://user:pass@localhost/db",
    jwt_secret_key="your-secret-key",
    encryption_key="your-encryption-key",
    email_backend="console",
    timezone="UTC",
)

# Get settings
settings = get_settings()
```

**When to use programmatic configuration:**
- Production applications (explicit and predictable)
- Applications with multiple environments
- Applications that need to configure settings dynamically
- Testing environments (easier to override settings)

**Environment variables** (with `AUTH_` prefix) can be used as a fallback, but programmatic configuration is preferred for better control and explicit initialization.

## API Endpoints

### Authentication Endpoints

- `POST /auth/signup` - User registration

  ```json
  {
    "email": "user@example.com",
    "name": "John Doe",
    "password": "securepassword"
  }
  ```

- `POST /auth/login` - User login (if implemented)
- `POST /auth/social/{provider_type}/login` - Social authentication
  - Supported providers: `github`, `google`

  ```json
  {
    "code": "oauth_code_from_provider"
  }
  ```

## Database Configuration

### Supported Databases

- **PostgreSQL** (via asyncpg): `postgresql+asyncpg://user:pass@hostname/dbname`
- **MySQL** (via aiomysql): `mysql+aiomysql://user:pass@hostname/dbname?charset=utf8mb4`

Set the connection string via `configure_settings(database_url="...")` (recommended) or `AUTH_DATABASE_URL` environment variable.

### Database Migrations with Alembic

When using this package in your application, you must merge the package's metadata with your own application's metadata so Alembic can track both sets of tables.

#### Complete Example: `migrations/env.py`

```python
import asyncio
from logging.config import fileConfig

from alembic import context
from alembic.autogenerate.render import _repr_type
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.types import TypeDecorator

# IMPORTANT: Configure settings programmatically BEFORE importing models
from fastapi_auth import configure_settings, get_settings

configure_settings(
    database_url="postgresql+asyncpg://user:password@localhost/dbname",
    jwt_secret_key="your-secret-key",
    encryption_key="your-encryption-key",
    email_backend="console",
    timezone="UTC",
)

# Now import metadata from both your app and fastapi_auth
from fastapi_auth.models import get_metadata as get_auth_metadata
from myapp.models import Base as MyAppBase  # Your application's Base

# Merge metadata - Alembic will track tables from both sources
target_metadata = [MyAppBase.metadata, get_auth_metadata()]

# Alembic configuration
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def render_item_func(type_, object_, autogen_context):
    """Custom render function for TypeDecorator instances."""
    if type_ == "type" and isinstance(object_, TypeDecorator):
        return _repr_type(object_.impl, autogen_context)
    return False


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
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
    """Run migrations in 'online' mode."""
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
```

**Key Points:**
- Always call `configure_settings()` **before** importing any models
- Merge metadata using a list: `target_metadata = [MyAppBase.metadata, get_auth_metadata()]`
- This ensures Alembic tracks changes in both your models and fastapi_auth models
- Programmatic configuration is required for proper initialization

## Email Backends

### SMTP Backend

```env
AUTH_EMAIL_BACKEND=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@example.com
SMTP_USE_TLS=true
SMTP_TIMEOUT=10
```

### Azure Communication Services

```env
AUTH_EMAIL_BACKEND=azure
AZURE_EMAIL_SERVICE_NAME=your-service-name
AZURE_EMAIL_SERVICE_ENDPOINT=https://your-endpoint.communication.azure.com
AZURE_EMAIL_SERVICE_API_KEY=your-api-key
```

### Console Backend (Development)

```env
AUTH_EMAIL_BACKEND=console
```

## Field-Level Encryption

The package includes built-in field-level encryption for sensitive data using Fernet symmetric encryption.

### Setup

1. Generate an encryption key:

   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

2. Add to environment:

   ```env
   ENCRYPTION_KEY=<generated_key>
   ```

### Usage

```python
from fastapi_auth.models.common import EncryptedString
from sqlalchemy.orm import Mapped, mapped_column

class YourModel(Base):
    sensitive_field: Mapped[str] = mapped_column(EncryptedString, nullable=False)
```

**Note:** Encryption/decryption happens automatically. The same encryption key must be used consistently across all environments.

## Environment Variables

### Required Variables

- `AUTH_DATABASE_URL` - Database connection string
- `AUTH_TIMEZONE` - Timezone (defaults to "UTC")
- `JWT_SECRET_KEY` - Secret key for JWT token signing
- `ENCRYPTION_KEY` - Fernet encryption key for field-level encryption
- `AUTH_EMAIL_BACKEND` - Email backend (`smtp`, `console`, or `azure`)

### Optional Variables

- `AUTH_PROJECT_NAME` - Project name (defaults to "oblox-fastapi-auth")
- `AUTH_JWT_ALGORITHM` - JWT algorithm (defaults to "HS256")
- `AUTH_JWT_ACCESS_TOKEN_EXPIRE_MINUTES` - Access token expiry (defaults to 30)
- `AUTH_JWT_REFRESH_TOKEN_EXPIRE_MINUTES` - Refresh token expiry (defaults to 43200)
- `AUTH_JWT_AUDIENCE` - JWT audience (defaults to "oblox-fastapi-auth")
- `AUTH_PASSWORDLESS_LOGIN_ENABLED` - Enable passwordless login (defaults to False)
- `AUTH_EMAIL_VERIFICATION_REQUIRED` - Require email verification (defaults to False)

## Frontend Integration

See [FRONTEND_INTEGRATION.md](FRONTEND_INTEGRATION.md) for detailed frontend integration guide.

## CLI Commands

The package includes a CLI tool for managing users, roles, and permissions:

```bash
# Create a user
oblox-fastapi-auth-cli create-user <email> [--name NAME] [--password PASSWORD] [--is-staff]

# Create a role
oblox-fastapi-auth-cli create-role <name> [--description DESCRIPTION] [--is-active/--no-is-active]

# Create permission and assign to role
oblox-fastapi-auth-cli create-permission-for-role <role_name> <permission_name> <resource> <action> [--description DESCRIPTION]

# Add social provider
oblox-fastapi-auth-cli add-social-provider <provider_type> [--client-id CLIENT_ID] [--client-secret CLIENT_SECRET]
```

## Development

### Running Tests

```bash
uv run pytest
```

### Code Formatting

```bash
uv run ruff check .
uv run ruff format .
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
