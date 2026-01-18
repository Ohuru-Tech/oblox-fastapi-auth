import asyncio
import os
from pathlib import Path
from typing import AsyncGenerator

import pytest
from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from fastapi_auth.settings import Settings, configure_settings, get_settings

# Configure default test settings BEFORE importing anything that uses settings
# This prevents Settings validation errors during import
# Calculate TEST_DATABASE_URL first
env_file = Path(__file__).parent.parent / ".dev.env"
base_db_url = None
if env_file.exists():
    # Simple parsing of .dev.env file
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line.startswith("AUTH_DATABASE_URL=") and not line.startswith("#"):
                base_db_url = line.split("=", 1)[1].strip().strip('"').strip("'")
                break

if base_db_url:
    # Replace database name with test database name
    if "/" in base_db_url.rsplit("@", 1)[-1]:
        # Format: postgresql+asyncpg://user:pass@host:port/dbname
        parts = base_db_url.rsplit("/", 1)
        default_test_db_url = f"{parts[0]}/fastapi_auth_test"
    else:
        default_test_db_url = base_db_url.replace("fastapi-auth", "fastapi_auth_test")
else:
    default_test_db_url = os.getenv(
        "TEST_DATABASE_URL",
        os.getenv(
            "AUTH_DATABASE_URL",
            "postgresql+asyncpg://postgres:hello1234@localhost:5432/fastapi_auth_test",
        )
        .replace("/fastapi-auth", "/fastapi_auth_test")
        .replace("/fastapi_auth", "/fastapi_auth_test"),
    )

# Configure settings before any imports that use them
configure_settings(
    database_url=default_test_db_url,
    jwt_secret_key="test-secret-key-for-testing-only",
    jwt_algorithm="HS256",
    jwt_access_token_expire_minutes=30,
    jwt_refresh_token_expire_minutes=60 * 24 * 30,
    jwt_audience="test-audience",
    encryption_key="test-encryption-key-32-bytes-long!!",
    email_backend="console",
    passwordless_login_enabled=False,
    email_verification_required=False,
    timezone="UTC",
)

# Now import modules that depend on settings
from fastapi_auth.database.db import get_session
from fastapi_auth.models import Base, User
from fastapi_auth.repositories.user_repository import UserRepository

# Import app after settings are configured
from main import app

fake = Faker()

# Use the same TEST_DATABASE_URL that was calculated above
TEST_DATABASE_URL = default_test_db_url


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


_test_db_created = False


@pytest.fixture(scope="function")
async def ensure_test_database():
    """Ensure test database exists before running tests."""
    global _test_db_created
    if _test_db_created:
        return

    import asyncpg

    # Parse database URL to get connection details
    # Format: postgresql+asyncpg://user:pass@host:port/dbname
    db_url_parts = TEST_DATABASE_URL.replace("postgresql+asyncpg://", "").split("/")
    if len(db_url_parts) < 2:
        return  # Can't parse, skip

    auth_part = db_url_parts[0]
    db_name = db_url_parts[1]

    if "@" in auth_part:
        user_pass, host_port = auth_part.rsplit("@", 1)
        if ":" in user_pass:
            user, password = user_pass.split(":", 1)
        else:
            user = user_pass
            password = None
        if ":" in host_port:
            host, port = host_port.split(":")
        else:
            host = host_port
            port = 5432
    else:
        return  # Can't parse

    try:
        # Connect to postgres database to create test database
        conn = await asyncpg.connect(
            host=host, port=int(port), user=user, password=password, database="postgres"
        )
        # Check if database exists
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", db_name
        )
        if not exists:
            await conn.execute(f'CREATE DATABASE "{db_name}"')
        await conn.close()
        _test_db_created = True
    except Exception:
        # If we can't create the database, tests will fail with a clear error
        pass


@pytest.fixture(scope="function")
async def test_engine(ensure_test_database):
    """Create a test database engine."""
    # Ensure all models are imported before creating tables
    from fastapi_auth.models.rbac import RolePermission, UserRole  # noqa: F401

    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    # Cleanup is handled by test_engine fixture


@pytest.fixture(scope="function")
def test_settings():
    """Override settings for testing."""
    # Configure test settings
    configure_settings(
        database_url=TEST_DATABASE_URL,
        jwt_secret_key="test-secret-key-for-testing-only",
        jwt_algorithm="HS256",
        jwt_access_token_expire_minutes=30,
        jwt_refresh_token_expire_minutes=60 * 24 * 30,
        jwt_audience="test-audience",
        encryption_key="test-encryption-key-32-bytes-long!!",
        email_backend="console",
        passwordless_login_enabled=False,
        email_verification_required=False,
        timezone="UTC",
    )

    yield get_settings()

    # Reset settings after test
    configure_settings()


@pytest.fixture(scope="function")
def test_client(test_settings) -> TestClient:
    """Create a test client for FastAPI."""

    # Override database dependency
    async def override_get_session():
        # This will be overridden per test that needs it
        pass

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as client:
        yield client

    # Clear overrides after test
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def db_session(test_session: AsyncSession, test_settings):
    """Provide a database session with dependency override."""

    async def override_get_session():
        yield test_session

    app.dependency_overrides[get_session] = override_get_session

    yield test_session

    # Rollback any uncommitted changes
    await test_session.rollback()
    app.dependency_overrides.clear()


@pytest.fixture
def mock_user_data():
    """Generate mock user data."""
    return {
        "email": fake.email(),
        "name": fake.name(),
        "password": "test_password_123",
        "profile_pic": fake.image_url(),
    }


@pytest.fixture
async def test_user(db_session: AsyncSession, mock_user_data):
    """Create a test user in the database."""
    from fastapi_auth.utils.password import hash_password

    user = User(
        email=mock_user_data["email"],
        name=mock_user_data["name"],
        password=hash_password(mock_user_data["password"])
        if mock_user_data["password"]
        else None,
        profile_pic=mock_user_data["profile_pic"],
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest.fixture
def mock_user_repository(mocker):
    """Create a mock user repository."""
    return mocker.Mock(spec=UserRepository)


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    settings = Settings(
        database_url=TEST_DATABASE_URL,
        jwt_secret_key="test-secret-key",
        jwt_algorithm="HS256",
        jwt_access_token_expire_minutes=30,
        jwt_refresh_token_expire_minutes=60 * 24 * 30,
        jwt_audience="test-audience",
        encryption_key="test-encryption-key-32-bytes-long!!",
        email_backend="console",
        passwordless_login_enabled=False,
        email_verification_required=False,
    )
    return settings
