"""
Models package for FastAPI Auth.

This package provides base models and utilities for user authentication.
"""

from fastapi_auth.models.base import Base
from fastapi_auth.models.rbac import Permission, Role, RolePermission, UserRole
from fastapi_auth.models.social_providers import SocialProvider
from fastapi_auth.models.user import User

__all__ = [
    "Base",
    "SocialProvider",
    "User",
    "Role",
    "Permission",
    "UserRole",
    "RolePermission",
]
