"""
FastAPI Auth - A comprehensive authentication package for FastAPI applications.

This package provides:
- User registration and authentication
- JWT token management
- Role-based access control (RBAC)
- Social media authentication (GitHub, Google)
- Password hashing and verification
- Email verification
- Field-level encryption for sensitive data
"""

from fastapi_auth.database.db import DatabaseSession, get_engine, get_session
from fastapi_auth.models import get_metadata
from fastapi_auth.routers.v1.auth_router import router as auth_router
from fastapi_auth.settings import Settings, configure_settings, get_settings

__version__ = "0.1.0"

__all__ = [
    "Settings",
    "configure_settings",
    "get_settings",
    "DatabaseSession",
    "get_engine",
    "get_session",
    "auth_router",
    "get_metadata",
]
