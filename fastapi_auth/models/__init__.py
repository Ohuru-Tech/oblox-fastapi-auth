"""
Models package for FastAPI Auth.

This package provides base models and utilities for user authentication.
"""

from sqlalchemy import MetaData

from fastapi_auth.models.base import Base
from fastapi_auth.models.rbac import Permission, Role, RolePermission, UserRole
from fastapi_auth.models.social_providers import SocialProvider
from fastapi_auth.models.user import User


def get_metadata() -> MetaData:
    """
    Get SQLAlchemy metadata for Alembic migrations.

    Returns the metadata object containing all table definitions from this package.
    This can be merged with your application's metadata for Alembic migrations.

    Returns:
        MetaData: SQLAlchemy metadata object containing all fastapi_auth tables

    Example:
        ```python
        from fastapi_auth.models import get_metadata as get_auth_metadata
        from myapp.models import Base as MyAppBase

        # Merge metadata for Alembic
        target_metadata = [MyAppBase.metadata, get_auth_metadata()]
        ```
    """
    return Base.metadata


__all__ = [
    "Base",
    "SocialProvider",
    "User",
    "Role",
    "Permission",
    "UserRole",
    "RolePermission",
    "get_metadata",
]
