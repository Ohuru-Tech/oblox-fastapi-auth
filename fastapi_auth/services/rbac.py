import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from fastapi_auth.models.user import User
from fastapi_auth.repositories.rbac_repository import (
    RBACRepository,
    get_rbac_repository,
)
from fastapi_auth.repositories.user_repository import (
    UserRepository,
    get_user_repository,
)
from fastapi_auth.settings import Settings, get_settings
from fastapi_auth.utils.logging import get_logger

logger = get_logger(__name__)
http_bearer = HTTPBearer()


async def _get_user_from_jwt(
    credentials: HTTPAuthorizationCredentials,
    config: Settings,
    user_repo: UserRepository,
) -> User:
    """Extract and validate user from JWT token."""
    if credentials.scheme.lower() != "bearer":
        logger.warning("Authentication attempt with non-bearer scheme")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        jwt_secret = config.jwt_secret_key
        algorithm = config.jwt_algorithm
        payload = jwt.decode(
            credentials.credentials, jwt_secret, algorithms=[algorithm]
        )
        # Try to get user_id from payload, fallback to email
        user_id = payload.get("id")
        if user_id:
            user = await user_repo.get_user_by_id(user_id)
        else:
            email = payload.get("sub")
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            user = await user_repo.get_user_by_email(email)
        if not user:
            logger.warning("User not found for token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        return user
    except jwt.ExpiredSignatureError:
        logger.warning("Authentication failed: Token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        logger.warning("Authentication failed: Invalid token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def _is_admin(user: User, rbac_repo: RBACRepository) -> bool:
    """Check if user has admin role."""
    roles = await rbac_repo.get_roles_by_user_id(user.id)
    return any(role.name == "admin" for role in roles)


async def _has_role(user: User, role_name: str, rbac_repo: RBACRepository) -> bool:
    """Check if user has specific role."""
    roles = await rbac_repo.get_roles_by_user_id(user.id)
    return any(role.name == role_name for role in roles)


async def _get_user_permissions(user: User, rbac_repo: RBACRepository) -> list:
    """Get all permissions for a user across all their roles."""
    permissions = await rbac_repo.get_permissions_by_user_id(user.id)
    return permissions


async def _has_permissions(
    user: User, permission_names: list[str], rbac_repo: RBACRepository
) -> bool:
    """Check if user has all required permissions. Admin bypasses check."""
    if await _is_admin(user, rbac_repo):
        return True
    permissions = await _get_user_permissions(user, rbac_repo)
    user_permission_names = {perm.name for perm in permissions}
    return all(perm_name in user_permission_names for perm_name in permission_names)


def required_role(role_name: str):
    """Dependency factory function to require a specific role."""

    async def _required_role(
        credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
        config: Settings = Depends(get_settings),
        user_repo: UserRepository = Depends(get_user_repository),
        rbac_repo: RBACRepository = Depends(get_rbac_repository),
    ) -> User:
        """Dependency function to require a specific role."""
        user = await _get_user_from_jwt(credentials, config, user_repo)
        if await _is_admin(user, rbac_repo):
            logger.debug(f"Admin user bypassed role check: {user.email}")
            return user
        if not await _has_role(user, role_name, rbac_repo):
            logger.warning(
                f"Role check failed: User {user.email} does not have role {role_name}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {role_name}",
            )
        logger.debug(f"Role check passed: {user.email} has role {role_name}")
        return user

    return _required_role


async def required_admin(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    config: Settings = Depends(get_settings),
    user_repo: UserRepository = Depends(get_user_repository),
    rbac_repo: RBACRepository = Depends(get_rbac_repository),
) -> User:
    """Dependency function to require admin role."""
    user = await _get_user_from_jwt(credentials, config, user_repo)
    if not await _is_admin(user, rbac_repo):
        logger.warning(f"Admin check failed: User {user.email} is not an admin")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    logger.debug(f"Admin user authenticated: {user.email}")
    return user


def required_permissions(permission_names: list[str]):
    """Dependency factory function to require specific permissions."""

    async def _required_permissions(
        credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
        config: Settings = Depends(get_settings),
        user_repo: UserRepository = Depends(get_user_repository),
        rbac_repo: RBACRepository = Depends(get_rbac_repository),
    ) -> User:
        """Dependency function to require specific permissions."""
        user = await _get_user_from_jwt(credentials, config, user_repo)
        if not await _has_permissions(user, permission_names, rbac_repo):
            logger.warning(
                f"Permission check failed: User {user.email} does not have required permissions"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required permissions: {', '.join(permission_names)}",
            )
        logger.debug(f"Permission check passed: {user.email} has required permissions")
        return user

    return _required_permissions
