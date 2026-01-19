import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_auth.database.db import DatabaseSession
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


async def _get_user_from_token(
    token: str, config: Settings, user_repo: UserRepository
) -> User:
    """Extract and validate user from JWT token.

    Args:
        token: JWT token string
        config: Settings object with JWT configuration
        user_repo: UserRepository instance

    Returns:
        User object if authentication succeeds

    Raises:
        HTTPException: If authentication fails
    """
    try:
        jwt_secret = config.jwt_secret_key
        algorithm = config.jwt_algorithm
        payload = jwt.decode(token, jwt_secret, algorithms=[algorithm])

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


async def _get_user_from_request(
    request: Request, session: AsyncSession | None = None
) -> User:
    """Extract and validate user from JWT token in request Authorization header.

    Args:
        request: FastAPI Request object
        session: Optional database session. If provided, uses this session without
                 creating/closing its own. If None, creates its own session.

    Returns:
        User object if authentication succeeds

    Raises:
        HTTPException: If authentication fails
    """
    # Extract Authorization header
    auth_header = request.headers.get("authorization")
    if not auth_header:
        logger.warning("Authentication attempt without Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Parse Bearer token
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        logger.warning("Authentication attempt with non-bearer scheme")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]

    # Get settings
    config = get_settings()

    # If session is provided, use it; otherwise create our own
    if session is not None:
        # Use provided session without creating/closing it
        user_repo = UserRepository(database=session)
        return await _get_user_from_token(token, config, user_repo)
    else:
        # Create our own session for backward compatibility
        db_session = DatabaseSession(config)

        async with db_session.SessionLocal() as session:
            user_repo = UserRepository(database=session)
            return await _get_user_from_token(token, config, user_repo)


async def check_admin_from_request(request: Request) -> User:
    """Check if user from request has admin role. Returns User or raises HTTPException."""
    db_session = DatabaseSession(get_settings())

    async with db_session.SessionLocal() as session:
        user = await _get_user_from_request(request, session=session)
        rbac_repo = RBACRepository(database=session)

        if not await _is_admin(user, rbac_repo):
            logger.warning(f"Admin check failed: User {user.email} is not an admin")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required",
            )
        logger.debug(f"Admin user authenticated: {user.email}")
        return user


async def check_role_from_request(request: Request, role_name: str) -> User:
    """Check if user from request has required role. Returns User or raises HTTPException."""
    db_session = DatabaseSession(get_settings())

    async with db_session.SessionLocal() as session:
        user = await _get_user_from_request(request, session=session)
        rbac_repo = RBACRepository(database=session)

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


async def check_permissions_from_request(
    request: Request, permission_names: list[str]
) -> User:
    """Check if user from request has required permissions. Returns User or raises HTTPException."""
    db_session = DatabaseSession(get_settings())

    async with db_session.SessionLocal() as session:
        user = await _get_user_from_request(request, session=session)
        rbac_repo = RBACRepository(database=session)

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
