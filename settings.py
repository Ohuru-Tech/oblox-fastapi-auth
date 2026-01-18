import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Literal, Optional, Union

from cryptography.fernet import Fernet
from pydantic_extra_types.timezone_name import TimeZoneName
from pydantic_settings import BaseSettings, SettingsConfigDict

ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")
BASE_DIR = Path(__file__).parent

_runtime_overrides: Dict[str, Any] = {}


# Global state to hold the configured env file path
class Settings(BaseSettings):
    # Basic Settings
    database_url: str
    timezone: TimeZoneName = "UTC"
    project_name: str = "oblox-fastapi-auth"

    # JWT Settings
    jwt_secret_key: str = "sample-secret-key-dont-use-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30  # 30 minutes
    jwt_refresh_token_expire_minutes: int = 60 * 24 * 30  # 30 days
    jwt_audience: str = "oblox-fastapi-auth"

    # Encryption Settings
    encryption_key: str = Fernet.generate_key().decode()

    # Configuring email backends
    email_backend: Union[Literal["smtp"], Literal["azure"], Literal["console"]] = "smtp"

    # Configure the template directory to use, we will have default as well
    templates_dir: str = os.path.join(Path(__file__).parent, "templates")

    # SMTP Settings ( only required if email_backend is "smtp" )
    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    smtp_use_tls: bool = True
    smtp_timeout: int = 10

    # Azure Email Settings ( only required if email_backend is "azure" )
    azure_email_service_name: str | None = None
    azure_email_service_endpoint: str | None = None
    azure_email_service_api_key: str | None = None

    # Custom Model Settings (optional - use default models if not specified)
    custom_user_model: Optional[str] = (
        None  # Import path for custom User model (e.g., "myapp.models.CustomUser")
    )
    custom_user_profile_model: Optional[str] = (
        None  # Import path for custom UserProfile model
    )

    # Auth settings for password, emails etc
    passwordless_login_enabled: bool = False
    email_verification_required: bool = False

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / f".{ENVIRONMENT}.env",
        env_file_encoding="utf-8",
        env_prefix="AUTH_",
    )


def configure_settings(**kwargs):
    """
    Configure settings with runtime overrides.

    Updates the runtime overrides dictionary and clears the settings cache.
    Runtime overrides take precedence over environment variables.

    Args:
        **kwargs: Settings to override (e.g., database_url="...", jwt_secret_key="...")

    Example:
        configure_settings(
            database_url="postgresql+asyncpg://user:pass@localhost/db",
            jwt_secret_key="your-secret-key"
        )
    """
    global _runtime_overrides
    _runtime_overrides.update(kwargs)
    get_settings.cache_clear()


@lru_cache
def get_settings() -> Settings:
    """
    Get the current settings.
    If `configure_settings()` was called, runtime overrides take precedence.
    Otherwise, loads from environment variables (defaults).
    """
    return Settings(**_runtime_overrides)
