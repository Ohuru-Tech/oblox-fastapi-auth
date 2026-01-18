from enum import EnumType
from typing import Type

from cryptography.fernet import Fernet
from sqlalchemy import Enum, String
from sqlalchemy.types import TypeDecorator

from fastapi_auth.settings import get_settings


def create_enum_column(enum_class: Type[EnumType], name: str = None):
    """
    Creates a reusable SQLAlchemy Enum column with the standard pattern:
    - create_type=False
    - values_callable that extracts enum values

    Args:
        enum_class: The enum class to use
        name: Optional name for the enum type (defaults to enum class name)

    Returns:
        SQLAlchemy Enum column definition
    """
    return Enum(
        enum_class,
        name=name or enum_class.__name__.lower(),
        create_type=False,
        values_callable=lambda enum_cls: [member.value for member in enum_cls],
    )


class EncryptedString(TypeDecorator):
    """
    Encrypts/decrypts string values automatically using Fernet symmetric encryption.

    Values are encrypted when writing to the database and decrypted when reading.
    The encryption key is retrieved from settings.encryption_key.
    """

    impl = String
    cache_ok = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Don't initialize cipher here - do it lazily when needed
        self._cipher = None

    def _get_cipher(self):
        """Get or create the Fernet cipher instance."""
        if self._cipher is None:
            settings = get_settings()
            key = settings.encryption_key.encode()
            self._cipher = Fernet(key)
        return self._cipher

    def process_bind_param(self, value, dialect):
        """Encrypt when writing to DB"""
        if value is not None:
            return self._get_cipher().encrypt(value.encode()).decode()
        return value

    def process_result_value(self, value, dialect):
        """Decrypt when reading from DB"""
        if value is not None:
            return self._get_cipher().decrypt(value.encode()).decode()
        return value
