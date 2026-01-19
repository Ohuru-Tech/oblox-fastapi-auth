import datetime
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo

import jwt
import pytest
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials

from fastapi_auth.models.rbac import Permission, Role
from fastapi_auth.models.user import User
from fastapi_auth.services.rbac import (
    _get_user_from_jwt,
    _get_user_from_request,
    _has_permissions,
    _has_role,
    _is_admin,
    check_admin_from_request,
    check_permissions_from_request,
    check_role_from_request,
    required_admin,
    required_permissions,
    required_role,
)


class TestIsAdmin:
    """Test _is_admin helper function."""

    @pytest.mark.asyncio
    async def test_is_admin_with_admin_user(self):
        """Test _is_admin returns True for admin user."""
        user = User(id=1, email="admin@example.com")
        admin_role = Role(id=1, name="admin")

        mock_rbac_repo = AsyncMock()
        mock_rbac_repo.get_roles_by_user_id.return_value = [admin_role]

        result = await _is_admin(user, mock_rbac_repo)

        assert result is True
        mock_rbac_repo.get_roles_by_user_id.assert_called_once_with(user.id)

    @pytest.mark.asyncio
    async def test_is_admin_with_non_admin_user(self):
        """Test _is_admin returns False for non-admin user."""
        user = User(id=1, email="user@example.com")
        regular_role = Role(id=1, name="user")

        mock_rbac_repo = AsyncMock()
        mock_rbac_repo.get_roles_by_user_id.return_value = [regular_role]

        result = await _is_admin(user, mock_rbac_repo)

        assert result is False

    @pytest.mark.asyncio
    async def test_is_admin_with_no_roles(self):
        """Test _is_admin returns False for user with no roles."""
        user = User(id=1, email="user@example.com")

        mock_rbac_repo = AsyncMock()
        mock_rbac_repo.get_roles_by_user_id.return_value = []

        result = await _is_admin(user, mock_rbac_repo)

        assert result is False


class TestHasRole:
    """Test _has_role helper function."""

    @pytest.mark.asyncio
    async def test_has_role_with_matching_role(self):
        """Test _has_role returns True when user has the role."""
        user = User(id=1, email="user@example.com")
        role = Role(id=1, name="editor")

        mock_rbac_repo = AsyncMock()
        mock_rbac_repo.get_roles_by_user_id.return_value = [role]

        result = await _has_role(user, "editor", mock_rbac_repo)

        assert result is True

    @pytest.mark.asyncio
    async def test_has_role_without_matching_role(self):
        """Test _has_role returns False when user doesn't have the role."""
        user = User(id=1, email="user@example.com")
        role = Role(id=1, name="viewer")

        mock_rbac_repo = AsyncMock()
        mock_rbac_repo.get_roles_by_user_id.return_value = [role]

        result = await _has_role(user, "editor", mock_rbac_repo)

        assert result is False


class TestHasPermissions:
    """Test _has_permissions helper function."""

    @pytest.mark.asyncio
    async def test_has_permissions_with_admin_user(self):
        """Test admin user bypasses permission check."""
        user = User(id=1, email="admin@example.com")
        admin_role = Role(id=1, name="admin")

        mock_rbac_repo = AsyncMock()
        mock_rbac_repo.get_roles_by_user_id.return_value = [admin_role]

        result = await _has_permissions(user, ["read:users"], mock_rbac_repo)

        assert result is True

    @pytest.mark.asyncio
    async def test_has_permissions_with_all_permissions(self):
        """Test _has_permissions returns True when user has all permissions."""
        user = User(id=1, email="user@example.com")
        perm1 = Permission(id=1, name="read:users", resource="users", action="read")
        perm2 = Permission(id=2, name="write:users", resource="users", action="write")

        mock_rbac_repo = AsyncMock()
        mock_rbac_repo.get_roles_by_user_id.return_value = []
        mock_rbac_repo.get_permissions_by_user_id.return_value = [perm1, perm2]

        result = await _has_permissions(
            user, ["read:users", "write:users"], mock_rbac_repo
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_has_permissions_with_missing_permission(self):
        """Test _has_permissions returns False when user is missing a permission."""
        user = User(id=1, email="user@example.com")
        perm1 = Permission(id=1, name="read:users", resource="users", action="read")

        mock_rbac_repo = AsyncMock()
        mock_rbac_repo.get_roles_by_user_id.return_value = []
        mock_rbac_repo.get_permissions_by_user_id.return_value = [perm1]

        result = await _has_permissions(
            user, ["read:users", "write:users"], mock_rbac_repo
        )

        assert result is False


class TestGetUserFromJWT:
    """Test _get_user_from_jwt helper function."""

    @pytest.mark.asyncio
    async def test_get_user_from_jwt_with_valid_token(self, mock_settings):
        """Test _get_user_from_jwt with valid token."""
        user = User(id=1, email="test@example.com")

        tz = ZoneInfo(mock_settings.timezone)
        payload = {
            "sub": user.email,
            "exp": datetime.datetime.now(tz=tz) + timedelta(minutes=30),
        }
        token = jwt.encode(
            payload, mock_settings.jwt_secret_key, algorithm=mock_settings.jwt_algorithm
        )

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        mock_user_repo = AsyncMock()
        mock_user_repo.get_user_by_email.return_value = user

        result = await _get_user_from_jwt(credentials, mock_settings, mock_user_repo)

        assert result.email == user.email

    @pytest.mark.asyncio
    async def test_get_user_from_jwt_with_invalid_scheme(self, mock_settings):
        """Test _get_user_from_jwt with invalid scheme raises HTTPException."""
        credentials = HTTPAuthorizationCredentials(scheme="Basic", credentials="token")
        mock_user_repo = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await _get_user_from_jwt(credentials, mock_settings, mock_user_repo)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_user_from_jwt_with_expired_token(self, mock_settings):
        """Test _get_user_from_jwt with expired token raises HTTPException."""
        payload = {
            "sub": "test@example.com",
            "exp": datetime.datetime.now(tz=ZoneInfo(mock_settings.timezone))
            - timedelta(hours=1),
        }
        token = jwt.encode(
            payload, mock_settings.jwt_secret_key, algorithm=mock_settings.jwt_algorithm
        )

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        mock_user_repo = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await _get_user_from_jwt(credentials, mock_settings, mock_user_repo)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "expired" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_get_user_from_jwt_with_nonexistent_user(self, mock_settings):
        """Test _get_user_from_jwt with valid token but nonexistent user."""
        tz = ZoneInfo(mock_settings.timezone)
        payload = {
            "sub": "nonexistent@example.com",
            "exp": datetime.datetime.now(tz=tz) + timedelta(minutes=30),
        }
        token = jwt.encode(
            payload, mock_settings.jwt_secret_key, algorithm=mock_settings.jwt_algorithm
        )

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        mock_user_repo = AsyncMock()
        mock_user_repo.get_user_by_email.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await _get_user_from_jwt(credentials, mock_settings, mock_user_repo)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestRequiredAdmin:
    """Test required_admin dependency function."""

    @pytest.mark.asyncio
    async def test_required_admin_with_admin_user(self, mock_settings):
        """Test required_admin with admin user returns user."""
        user = User(id=1, email="admin@example.com")
        admin_role = Role(id=1, name="admin")

        tz = ZoneInfo(mock_settings.timezone)
        payload = {
            "sub": user.email,
            "exp": datetime.datetime.now(tz=tz) + timedelta(minutes=30),
        }
        token = jwt.encode(
            payload, mock_settings.jwt_secret_key, algorithm=mock_settings.jwt_algorithm
        )

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        mock_user_repo = AsyncMock()
        mock_user_repo.get_user_by_email.return_value = user

        mock_rbac_repo = AsyncMock()
        mock_rbac_repo.get_roles_by_user_id.return_value = [admin_role]

        result = await required_admin(
            credentials=credentials,
            config=mock_settings,
            user_repo=mock_user_repo,
            rbac_repo=mock_rbac_repo,
        )

        assert result.email == user.email

    @pytest.mark.asyncio
    async def test_required_admin_with_non_admin_user(self, mock_settings):
        """Test required_admin with non-admin user raises HTTPException."""
        user = User(id=1, email="user@example.com")
        regular_role = Role(id=1, name="user")

        tz = ZoneInfo(mock_settings.timezone)
        payload = {
            "sub": user.email,
            "exp": datetime.datetime.now(tz=tz) + timedelta(minutes=30),
        }
        token = jwt.encode(
            payload, mock_settings.jwt_secret_key, algorithm=mock_settings.jwt_algorithm
        )

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        mock_user_repo = AsyncMock()
        mock_user_repo.get_user_by_email.return_value = user

        mock_rbac_repo = AsyncMock()
        mock_rbac_repo.get_roles_by_user_id.return_value = [regular_role]

        with pytest.raises(HTTPException) as exc_info:
            await required_admin(
                credentials=credentials,
                config=mock_settings,
                user_repo=mock_user_repo,
                rbac_repo=mock_rbac_repo,
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "admin" in exc_info.value.detail.lower()


class TestRequiredRole:
    """Test required_role dependency function."""

    @pytest.mark.asyncio
    async def test_required_role_with_user_having_role(self, mock_settings):
        """Test required_role with user having the role returns user."""
        user = User(id=1, email="editor@example.com")
        editor_role = Role(id=1, name="editor")

        tz = ZoneInfo(mock_settings.timezone)
        payload = {
            "sub": user.email,
            "exp": datetime.datetime.now(tz=tz) + timedelta(minutes=30),
        }
        token = jwt.encode(
            payload, mock_settings.jwt_secret_key, algorithm=mock_settings.jwt_algorithm
        )

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        mock_user_repo = AsyncMock()
        mock_user_repo.get_user_by_email.return_value = user

        mock_rbac_repo = AsyncMock()
        mock_rbac_repo.get_roles_by_user_id.return_value = [editor_role]

        role_dependency = required_role("editor")
        result = await role_dependency(
            credentials=credentials,
            config=mock_settings,
            user_repo=mock_user_repo,
            rbac_repo=mock_rbac_repo,
        )

        assert result.email == user.email

    @pytest.mark.asyncio
    async def test_required_role_with_admin_bypass(self, mock_settings):
        """Test required_role with admin user bypasses role check."""
        user = User(id=1, email="admin@example.com")
        admin_role = Role(id=1, name="admin")

        tz = ZoneInfo(mock_settings.timezone)
        payload = {
            "sub": user.email,
            "exp": datetime.datetime.now(tz=tz) + timedelta(minutes=30),
        }
        token = jwt.encode(
            payload, mock_settings.jwt_secret_key, algorithm=mock_settings.jwt_algorithm
        )

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        mock_user_repo = AsyncMock()
        mock_user_repo.get_user_by_email.return_value = user

        mock_rbac_repo = AsyncMock()
        mock_rbac_repo.get_roles_by_user_id.return_value = [admin_role]

        role_dependency = required_role("editor")
        result = await role_dependency(
            credentials=credentials,
            config=mock_settings,
            user_repo=mock_user_repo,
            rbac_repo=mock_rbac_repo,
        )

        assert result.email == user.email

    @pytest.mark.asyncio
    async def test_required_role_with_user_missing_role(self, mock_settings):
        """Test required_role with user missing role raises HTTPException."""
        user = User(id=1, email="user@example.com")
        viewer_role = Role(id=1, name="viewer")

        tz = ZoneInfo(mock_settings.timezone)
        payload = {
            "sub": user.email,
            "exp": datetime.datetime.now(tz=tz) + timedelta(minutes=30),
        }
        token = jwt.encode(
            payload, mock_settings.jwt_secret_key, algorithm=mock_settings.jwt_algorithm
        )

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        mock_user_repo = AsyncMock()
        mock_user_repo.get_user_by_email.return_value = user

        mock_rbac_repo = AsyncMock()
        mock_rbac_repo.get_roles_by_user_id.return_value = [viewer_role]

        role_dependency = required_role("editor")

        with pytest.raises(HTTPException) as exc_info:
            await role_dependency(
                credentials=credentials,
                config=mock_settings,
                user_repo=mock_user_repo,
                rbac_repo=mock_rbac_repo,
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestRequiredPermissions:
    """Test required_permissions dependency function."""

    @pytest.mark.asyncio
    async def test_required_permissions_with_user_having_permissions(
        self, mock_settings
    ):
        """Test required_permissions with user having permissions returns user."""
        user = User(id=1, email="user@example.com")
        perm1 = Permission(id=1, name="read:users", resource="users", action="read")
        perm2 = Permission(id=2, name="write:users", resource="users", action="write")

        tz = ZoneInfo(mock_settings.timezone)
        payload = {
            "sub": user.email,
            "exp": datetime.datetime.now(tz=tz) + timedelta(minutes=30),
        }
        token = jwt.encode(
            payload, mock_settings.jwt_secret_key, algorithm=mock_settings.jwt_algorithm
        )

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        mock_user_repo = AsyncMock()
        mock_user_repo.get_user_by_email.return_value = user

        mock_rbac_repo = AsyncMock()
        mock_rbac_repo.get_roles_by_user_id.return_value = []
        mock_rbac_repo.get_permissions_by_user_id.return_value = [perm1, perm2]

        perm_dependency = required_permissions(["read:users", "write:users"])
        result = await perm_dependency(
            credentials=credentials,
            config=mock_settings,
            user_repo=mock_user_repo,
            rbac_repo=mock_rbac_repo,
        )

        assert result.email == user.email

    @pytest.mark.asyncio
    async def test_required_permissions_with_admin_bypass(self, mock_settings):
        """Test required_permissions with admin user bypasses permission check."""
        user = User(id=1, email="admin@example.com")
        admin_role = Role(id=1, name="admin")

        tz = ZoneInfo(mock_settings.timezone)
        payload = {
            "sub": user.email,
            "exp": datetime.datetime.now(tz=tz) + timedelta(minutes=30),
        }
        token = jwt.encode(
            payload, mock_settings.jwt_secret_key, algorithm=mock_settings.jwt_algorithm
        )

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        mock_user_repo = AsyncMock()
        mock_user_repo.get_user_by_email.return_value = user

        mock_rbac_repo = AsyncMock()
        mock_rbac_repo.get_roles_by_user_id.return_value = [admin_role]

        perm_dependency = required_permissions(["read:users", "write:users"])
        result = await perm_dependency(
            credentials=credentials,
            config=mock_settings,
            user_repo=mock_user_repo,
            rbac_repo=mock_rbac_repo,
        )

        assert result.email == user.email

    @pytest.mark.asyncio
    async def test_required_permissions_with_missing_permission(self, mock_settings):
        """Test required_permissions with missing permission raises HTTPException."""
        user = User(id=1, email="user@example.com")
        perm1 = Permission(id=1, name="read:users", resource="users", action="read")

        tz = ZoneInfo(mock_settings.timezone)
        payload = {
            "sub": user.email,
            "exp": datetime.datetime.now(tz=tz) + timedelta(minutes=30),
        }
        token = jwt.encode(
            payload, mock_settings.jwt_secret_key, algorithm=mock_settings.jwt_algorithm
        )

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        mock_user_repo = AsyncMock()
        mock_user_repo.get_user_by_email.return_value = user

        mock_rbac_repo = AsyncMock()
        mock_rbac_repo.get_roles_by_user_id.return_value = []
        mock_rbac_repo.get_permissions_by_user_id.return_value = [perm1]

        perm_dependency = required_permissions(["read:users", "write:users"])

        with pytest.raises(HTTPException) as exc_info:
            await perm_dependency(
                credentials=credentials,
                config=mock_settings,
                user_repo=mock_user_repo,
                rbac_repo=mock_rbac_repo,
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestGetUserFromRequest:
    """Test _get_user_from_request helper function."""

    @pytest.mark.asyncio
    async def test_get_user_from_request_with_valid_token(self, mock_settings):
        """Test _get_user_from_request with valid token."""
        user = User(id=1, email="test@example.com")

        tz = ZoneInfo(mock_settings.timezone)
        payload = {
            "sub": user.email,
            "exp": datetime.datetime.now(tz=tz) + timedelta(minutes=30),
        }
        token = jwt.encode(
            payload, mock_settings.jwt_secret_key, algorithm=mock_settings.jwt_algorithm
        )

        request = MagicMock(spec=Request)
        request.headers.get.return_value = f"Bearer {token}"

        mock_session = AsyncMock()
        mock_user_repo = AsyncMock()
        mock_user_repo.get_user_by_email.return_value = user

        # Create async context manager mock
        async_context_manager = AsyncMock()
        async_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
        async_context_manager.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "fastapi_auth.services.rbac.get_settings", return_value=mock_settings
        ):
            with patch("fastapi_auth.services.rbac.DatabaseSession") as mock_db_session:
                mock_db_session_instance = MagicMock()
                mock_db_session_instance.SessionLocal = MagicMock(
                    return_value=async_context_manager
                )
                mock_db_session.return_value = mock_db_session_instance

                with patch(
                    "fastapi_auth.services.rbac.UserRepository",
                    return_value=mock_user_repo,
                ):
                    from fastapi_auth.services.rbac import _get_user_from_request

                    result = await _get_user_from_request(request)

                    assert result.email == user.email

    @pytest.mark.asyncio
    async def test_get_user_from_request_with_missing_header(self, mock_settings):
        """Test _get_user_from_request with missing Authorization header."""
        request = MagicMock(spec=Request)
        request.headers.get.return_value = None

        with patch(
            "fastapi_auth.services.rbac.get_settings", return_value=mock_settings
        ):
            from fastapi_auth.services.rbac import _get_user_from_request

            with pytest.raises(HTTPException) as exc_info:
                await _get_user_from_request(request)

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "authorization" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_get_user_from_request_with_invalid_scheme(self, mock_settings):
        """Test _get_user_from_request with invalid scheme."""
        request = MagicMock(spec=Request)
        request.headers.get.return_value = "Basic token123"

        with patch(
            "fastapi_auth.services.rbac.get_settings", return_value=mock_settings
        ):
            from fastapi_auth.services.rbac import _get_user_from_request

            with pytest.raises(HTTPException) as exc_info:
                await _get_user_from_request(request)

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_user_from_request_with_expired_token(self, mock_settings):
        """Test _get_user_from_request with expired token."""
        payload = {
            "sub": "test@example.com",
            "exp": datetime.datetime.now(tz=ZoneInfo(mock_settings.timezone))
            - timedelta(hours=1),
        }
        token = jwt.encode(
            payload, mock_settings.jwt_secret_key, algorithm=mock_settings.jwt_algorithm
        )

        request = MagicMock(spec=Request)
        request.headers.get.return_value = f"Bearer {token}"

        mock_session = AsyncMock()

        # Create async context manager mock
        async_context_manager = AsyncMock()
        async_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
        async_context_manager.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "fastapi_auth.services.rbac.get_settings", return_value=mock_settings
        ):
            with patch("fastapi_auth.services.rbac.DatabaseSession") as mock_db_session:
                mock_db_session_instance = MagicMock()
                mock_db_session_instance.SessionLocal = MagicMock(
                    return_value=async_context_manager
                )
                mock_db_session.return_value = mock_db_session_instance

                with patch("fastapi_auth.services.rbac.UserRepository"):
                    from fastapi_auth.services.rbac import _get_user_from_request

                    with pytest.raises(HTTPException) as exc_info:
                        await _get_user_from_request(request)

                    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
                    assert "expired" in exc_info.value.detail.lower()


class TestCheckAdminFromRequest:
    """Test check_admin_from_request function."""

    @pytest.mark.asyncio
    async def test_check_admin_from_request_with_admin_user(self, mock_settings):
        """Test check_admin_from_request with admin user returns user."""
        user = User(id=1, email="admin@example.com")
        admin_role = Role(id=1, name="admin")

        tz = ZoneInfo(mock_settings.timezone)
        payload = {
            "sub": user.email,
            "exp": datetime.datetime.now(tz=tz) + timedelta(minutes=30),
        }
        token = jwt.encode(
            payload, mock_settings.jwt_secret_key, algorithm=mock_settings.jwt_algorithm
        )

        request = MagicMock(spec=Request)
        request.headers.get.return_value = f"Bearer {token}"

        mock_session = AsyncMock()
        mock_user_repo = AsyncMock()
        mock_user_repo.get_user_by_email.return_value = user

        mock_rbac_repo = AsyncMock()
        mock_rbac_repo.get_roles_by_user_id.return_value = [admin_role]

        # Create async context manager mock
        async_context_manager = AsyncMock()
        async_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
        async_context_manager.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "fastapi_auth.services.rbac.get_settings", return_value=mock_settings
        ):
            with patch("fastapi_auth.services.rbac.DatabaseSession") as mock_db_session:
                mock_db_session_instance = MagicMock()
                mock_db_session_instance.SessionLocal = MagicMock(
                    return_value=async_context_manager
                )
                mock_db_session.return_value = mock_db_session_instance

                with patch(
                    "fastapi_auth.services.rbac.UserRepository",
                    return_value=mock_user_repo,
                ):
                    with patch(
                        "fastapi_auth.services.rbac.RBACRepository",
                        return_value=mock_rbac_repo,
                    ):
                        result = await check_admin_from_request(request)

                        assert result.email == user.email

    @pytest.mark.asyncio
    async def test_check_admin_from_request_with_non_admin_user(self, mock_settings):
        """Test check_admin_from_request with non-admin user raises HTTPException."""
        user = User(id=1, email="user@example.com")
        regular_role = Role(id=1, name="user")

        tz = ZoneInfo(mock_settings.timezone)
        payload = {
            "sub": user.email,
            "exp": datetime.datetime.now(tz=tz) + timedelta(minutes=30),
        }
        token = jwt.encode(
            payload, mock_settings.jwt_secret_key, algorithm=mock_settings.jwt_algorithm
        )

        request = MagicMock(spec=Request)
        request.headers.get.return_value = f"Bearer {token}"

        mock_session = AsyncMock()
        mock_user_repo = AsyncMock()
        mock_user_repo.get_user_by_email.return_value = user

        mock_rbac_repo = AsyncMock()
        mock_rbac_repo.get_roles_by_user_id.return_value = [regular_role]

        # Create async context manager mock
        async_context_manager = AsyncMock()
        async_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
        async_context_manager.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "fastapi_auth.services.rbac.get_settings", return_value=mock_settings
        ):
            with patch("fastapi_auth.services.rbac.DatabaseSession") as mock_db_session:
                mock_db_session_instance = MagicMock()
                mock_db_session_instance.SessionLocal = MagicMock(
                    return_value=async_context_manager
                )
                mock_db_session.return_value = mock_db_session_instance

                with patch(
                    "fastapi_auth.services.rbac.UserRepository",
                    return_value=mock_user_repo,
                ):
                    with patch(
                        "fastapi_auth.services.rbac.RBACRepository",
                        return_value=mock_rbac_repo,
                    ):
                        with pytest.raises(HTTPException) as exc_info:
                            await check_admin_from_request(request)

                        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
                        assert "admin" in exc_info.value.detail.lower()


class TestCheckRoleFromRequest:
    """Test check_role_from_request function."""

    @pytest.mark.asyncio
    async def test_check_role_from_request_with_user_having_role(self, mock_settings):
        """Test check_role_from_request with user having the role returns user."""
        user = User(id=1, email="editor@example.com")
        editor_role = Role(id=1, name="editor")

        tz = ZoneInfo(mock_settings.timezone)
        payload = {
            "sub": user.email,
            "exp": datetime.datetime.now(tz=tz) + timedelta(minutes=30),
        }
        token = jwt.encode(
            payload, mock_settings.jwt_secret_key, algorithm=mock_settings.jwt_algorithm
        )

        request = MagicMock(spec=Request)
        request.headers.get.return_value = f"Bearer {token}"

        mock_session = AsyncMock()
        mock_user_repo = AsyncMock()
        mock_user_repo.get_user_by_email.return_value = user

        mock_rbac_repo = AsyncMock()
        mock_rbac_repo.get_roles_by_user_id.return_value = [editor_role]

        # Create async context manager mock
        async_context_manager = AsyncMock()
        async_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
        async_context_manager.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "fastapi_auth.services.rbac.get_settings", return_value=mock_settings
        ):
            with patch("fastapi_auth.services.rbac.DatabaseSession") as mock_db_session:
                mock_db_session_instance = MagicMock()
                mock_db_session_instance.SessionLocal = MagicMock(
                    return_value=async_context_manager
                )
                mock_db_session.return_value = mock_db_session_instance

                with patch(
                    "fastapi_auth.services.rbac.UserRepository",
                    return_value=mock_user_repo,
                ):
                    with patch(
                        "fastapi_auth.services.rbac.RBACRepository",
                        return_value=mock_rbac_repo,
                    ):
                        result = await check_role_from_request(request, "editor")

                        assert result.email == user.email

    @pytest.mark.asyncio
    async def test_check_role_from_request_with_admin_bypass(self, mock_settings):
        """Test check_role_from_request with admin user bypasses role check."""
        user = User(id=1, email="admin@example.com")
        admin_role = Role(id=1, name="admin")

        tz = ZoneInfo(mock_settings.timezone)
        payload = {
            "sub": user.email,
            "exp": datetime.datetime.now(tz=tz) + timedelta(minutes=30),
        }
        token = jwt.encode(
            payload, mock_settings.jwt_secret_key, algorithm=mock_settings.jwt_algorithm
        )

        request = MagicMock(spec=Request)
        request.headers.get.return_value = f"Bearer {token}"

        mock_session = AsyncMock()
        mock_user_repo = AsyncMock()
        mock_user_repo.get_user_by_email.return_value = user

        mock_rbac_repo = AsyncMock()
        mock_rbac_repo.get_roles_by_user_id.return_value = [admin_role]

        # Create async context manager mock
        async_context_manager = AsyncMock()
        async_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
        async_context_manager.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "fastapi_auth.services.rbac.get_settings", return_value=mock_settings
        ):
            with patch("fastapi_auth.services.rbac.DatabaseSession") as mock_db_session:
                mock_db_session_instance = MagicMock()
                mock_db_session_instance.SessionLocal = MagicMock(
                    return_value=async_context_manager
                )
                mock_db_session.return_value = mock_db_session_instance

                with patch(
                    "fastapi_auth.services.rbac.UserRepository",
                    return_value=mock_user_repo,
                ):
                    with patch(
                        "fastapi_auth.services.rbac.RBACRepository",
                        return_value=mock_rbac_repo,
                    ):
                        result = await check_role_from_request(request, "editor")

                        assert result.email == user.email

    @pytest.mark.asyncio
    async def test_check_role_from_request_with_user_missing_role(self, mock_settings):
        """Test check_role_from_request with user missing role raises HTTPException."""
        user = User(id=1, email="user@example.com")
        viewer_role = Role(id=1, name="viewer")

        tz = ZoneInfo(mock_settings.timezone)
        payload = {
            "sub": user.email,
            "exp": datetime.datetime.now(tz=tz) + timedelta(minutes=30),
        }
        token = jwt.encode(
            payload, mock_settings.jwt_secret_key, algorithm=mock_settings.jwt_algorithm
        )

        request = MagicMock(spec=Request)
        request.headers.get.return_value = f"Bearer {token}"

        mock_session = AsyncMock()
        mock_user_repo = AsyncMock()
        mock_user_repo.get_user_by_email.return_value = user

        mock_rbac_repo = AsyncMock()
        mock_rbac_repo.get_roles_by_user_id.return_value = [viewer_role]

        # Create async context manager mock
        async_context_manager = AsyncMock()
        async_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
        async_context_manager.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "fastapi_auth.services.rbac.get_settings", return_value=mock_settings
        ):
            with patch("fastapi_auth.services.rbac.DatabaseSession") as mock_db_session:
                mock_db_session_instance = MagicMock()
                mock_db_session_instance.SessionLocal = MagicMock(
                    return_value=async_context_manager
                )
                mock_db_session.return_value = mock_db_session_instance

                with patch(
                    "fastapi_auth.services.rbac.UserRepository",
                    return_value=mock_user_repo,
                ):
                    with patch(
                        "fastapi_auth.services.rbac.RBACRepository",
                        return_value=mock_rbac_repo,
                    ):
                        with pytest.raises(HTTPException) as exc_info:
                            await check_role_from_request(request, "editor")

                        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestCheckPermissionsFromRequest:
    """Test check_permissions_from_request function."""

    @pytest.mark.asyncio
    async def test_check_permissions_from_request_with_user_having_permissions(
        self, mock_settings
    ):
        """Test check_permissions_from_request with user having permissions returns user."""
        user = User(id=1, email="user@example.com")
        perm1 = Permission(id=1, name="read:users", resource="users", action="read")
        perm2 = Permission(id=2, name="write:users", resource="users", action="write")

        tz = ZoneInfo(mock_settings.timezone)
        payload = {
            "sub": user.email,
            "exp": datetime.datetime.now(tz=tz) + timedelta(minutes=30),
        }
        token = jwt.encode(
            payload, mock_settings.jwt_secret_key, algorithm=mock_settings.jwt_algorithm
        )

        request = MagicMock(spec=Request)
        request.headers.get.return_value = f"Bearer {token}"

        mock_session = AsyncMock()
        mock_user_repo = AsyncMock()
        mock_user_repo.get_user_by_email.return_value = user

        mock_rbac_repo = AsyncMock()
        mock_rbac_repo.get_roles_by_user_id.return_value = []
        mock_rbac_repo.get_permissions_by_user_id.return_value = [perm1, perm2]

        # Create async context manager mock
        async_context_manager = AsyncMock()
        async_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
        async_context_manager.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "fastapi_auth.services.rbac.get_settings", return_value=mock_settings
        ):
            with patch("fastapi_auth.services.rbac.DatabaseSession") as mock_db_session:
                mock_db_session_instance = MagicMock()
                mock_db_session_instance.SessionLocal = MagicMock(
                    return_value=async_context_manager
                )
                mock_db_session.return_value = mock_db_session_instance

                with patch(
                    "fastapi_auth.services.rbac.UserRepository",
                    return_value=mock_user_repo,
                ):
                    with patch(
                        "fastapi_auth.services.rbac.RBACRepository",
                        return_value=mock_rbac_repo,
                    ):
                        result = await check_permissions_from_request(
                            request, ["read:users", "write:users"]
                        )

                        assert result.email == user.email

    @pytest.mark.asyncio
    async def test_check_permissions_from_request_with_admin_bypass(
        self, mock_settings
    ):
        """Test check_permissions_from_request with admin user bypasses permission check."""
        user = User(id=1, email="admin@example.com")
        admin_role = Role(id=1, name="admin")

        tz = ZoneInfo(mock_settings.timezone)
        payload = {
            "sub": user.email,
            "exp": datetime.datetime.now(tz=tz) + timedelta(minutes=30),
        }
        token = jwt.encode(
            payload, mock_settings.jwt_secret_key, algorithm=mock_settings.jwt_algorithm
        )

        request = MagicMock(spec=Request)
        request.headers.get.return_value = f"Bearer {token}"

        mock_session = AsyncMock()
        mock_user_repo = AsyncMock()
        mock_user_repo.get_user_by_email.return_value = user

        mock_rbac_repo = AsyncMock()
        mock_rbac_repo.get_roles_by_user_id.return_value = [admin_role]

        # Create async context manager mock
        async_context_manager = AsyncMock()
        async_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
        async_context_manager.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "fastapi_auth.services.rbac.get_settings", return_value=mock_settings
        ):
            with patch("fastapi_auth.services.rbac.DatabaseSession") as mock_db_session:
                mock_db_session_instance = MagicMock()
                mock_db_session_instance.SessionLocal = MagicMock(
                    return_value=async_context_manager
                )
                mock_db_session.return_value = mock_db_session_instance

                with patch(
                    "fastapi_auth.services.rbac.UserRepository",
                    return_value=mock_user_repo,
                ):
                    with patch(
                        "fastapi_auth.services.rbac.RBACRepository",
                        return_value=mock_rbac_repo,
                    ):
                        result = await check_permissions_from_request(
                            request, ["read:users", "write:users"]
                        )

                        assert result.email == user.email

    @pytest.mark.asyncio
    async def test_check_permissions_from_request_with_missing_permission(
        self, mock_settings
    ):
        """Test check_permissions_from_request with missing permission raises HTTPException."""
        user = User(id=1, email="user@example.com")
        perm1 = Permission(id=1, name="read:users", resource="users", action="read")

        tz = ZoneInfo(mock_settings.timezone)
        payload = {
            "sub": user.email,
            "exp": datetime.datetime.now(tz=tz) + timedelta(minutes=30),
        }
        token = jwt.encode(
            payload, mock_settings.jwt_secret_key, algorithm=mock_settings.jwt_algorithm
        )

        request = MagicMock(spec=Request)
        request.headers.get.return_value = f"Bearer {token}"

        mock_session = AsyncMock()
        mock_user_repo = AsyncMock()
        mock_user_repo.get_user_by_email.return_value = user

        mock_rbac_repo = AsyncMock()
        mock_rbac_repo.get_roles_by_user_id.return_value = []
        mock_rbac_repo.get_permissions_by_user_id.return_value = [perm1]

        # Create async context manager mock
        async_context_manager = AsyncMock()
        async_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
        async_context_manager.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "fastapi_auth.services.rbac.get_settings", return_value=mock_settings
        ):
            with patch("fastapi_auth.services.rbac.DatabaseSession") as mock_db_session:
                mock_db_session_instance = MagicMock()
                mock_db_session_instance.SessionLocal = MagicMock(
                    return_value=async_context_manager
                )
                mock_db_session.return_value = mock_db_session_instance

                with patch(
                    "fastapi_auth.services.rbac.UserRepository",
                    return_value=mock_user_repo,
                ):
                    with patch(
                        "fastapi_auth.services.rbac.RBACRepository",
                        return_value=mock_rbac_repo,
                    ):
                        with pytest.raises(HTTPException) as exc_info:
                            await check_permissions_from_request(
                                request, ["read:users", "write:users"]
                            )

                        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestSessionLogic:
    """Test session management logic in check_* functions."""

    @pytest.mark.asyncio
    async def test_get_user_from_request_with_provided_session(self, mock_settings):
        """Test _get_user_from_request uses provided session and doesn't create its own."""
        user = User(id=1, email="test@example.com")

        tz = ZoneInfo(mock_settings.timezone)
        payload = {
            "sub": user.email,
            "exp": datetime.datetime.now(tz=tz) + timedelta(minutes=30),
        }
        token = jwt.encode(
            payload, mock_settings.jwt_secret_key, algorithm=mock_settings.jwt_algorithm
        )

        request = MagicMock(spec=Request)
        request.headers.get.return_value = f"Bearer {token}"

        # Create a mock session that will be passed in
        mock_session = AsyncMock()
        mock_user_repo = AsyncMock()
        mock_user_repo.get_user_by_email.return_value = user

        with patch(
            "fastapi_auth.services.rbac.get_settings", return_value=mock_settings
        ):
            # Mock UserRepository to verify it uses the provided session
            with patch(
                "fastapi_auth.services.rbac.UserRepository",
                return_value=mock_user_repo,
            ) as mock_user_repo_class:
                # Mock DatabaseSession to verify it's NOT called
                with patch(
                    "fastapi_auth.services.rbac.DatabaseSession"
                ) as mock_db_session:
                    result = await _get_user_from_request(request, session=mock_session)

                    # Verify user was retrieved
                    assert result.email == user.email

                    # Verify UserRepository was called with the provided session
                    mock_user_repo_class.assert_called_once_with(database=mock_session)

                    # Verify DatabaseSession was NOT called (no new session created)
                    mock_db_session.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_user_from_request_creates_own_session(self, mock_settings):
        """Test _get_user_from_request creates its own session when none is provided."""
        user = User(id=1, email="test@example.com")

        tz = ZoneInfo(mock_settings.timezone)
        payload = {
            "sub": user.email,
            "exp": datetime.datetime.now(tz=tz) + timedelta(minutes=30),
        }
        token = jwt.encode(
            payload, mock_settings.jwt_secret_key, algorithm=mock_settings.jwt_algorithm
        )

        request = MagicMock(spec=Request)
        request.headers.get.return_value = f"Bearer {token}"

        mock_session = AsyncMock()
        mock_user_repo = AsyncMock()
        mock_user_repo.get_user_by_email.return_value = user

        # Create async context manager mock
        async_context_manager = AsyncMock()
        async_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
        async_context_manager.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "fastapi_auth.services.rbac.get_settings", return_value=mock_settings
        ):
            with patch("fastapi_auth.services.rbac.DatabaseSession") as mock_db_session:
                mock_db_session_instance = MagicMock()
                mock_db_session_instance.SessionLocal = MagicMock(
                    return_value=async_context_manager
                )
                mock_db_session.return_value = mock_db_session_instance

                with patch(
                    "fastapi_auth.services.rbac.UserRepository",
                    return_value=mock_user_repo,
                ):
                    result = await _get_user_from_request(request)

                    # Verify user was retrieved
                    assert result.email == user.email

                    # Verify DatabaseSession was called to create a new session
                    mock_db_session.assert_called_once_with(mock_settings)
                    mock_db_session_instance.SessionLocal.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_admin_from_request_uses_single_session(self, mock_settings):
        """Test check_admin_from_request uses a single session for both user retrieval and RBAC check."""
        user = User(id=1, email="admin@example.com")
        admin_role = Role(id=1, name="admin")

        tz = ZoneInfo(mock_settings.timezone)
        payload = {
            "sub": user.email,
            "exp": datetime.datetime.now(tz=tz) + timedelta(minutes=30),
        }
        token = jwt.encode(
            payload, mock_settings.jwt_secret_key, algorithm=mock_settings.jwt_algorithm
        )

        request = MagicMock(spec=Request)
        request.headers.get.return_value = f"Bearer {token}"

        mock_session = AsyncMock()
        mock_user_repo = AsyncMock()
        mock_user_repo.get_user_by_email.return_value = user

        mock_rbac_repo = AsyncMock()
        mock_rbac_repo.get_roles_by_user_id.return_value = [admin_role]

        # Create async context manager mock
        async_context_manager = AsyncMock()
        async_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
        async_context_manager.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "fastapi_auth.services.rbac.get_settings", return_value=mock_settings
        ):
            with patch("fastapi_auth.services.rbac.DatabaseSession") as mock_db_session:
                mock_db_session_instance = MagicMock()
                mock_db_session_instance.SessionLocal = MagicMock(
                    return_value=async_context_manager
                )
                mock_db_session.return_value = mock_db_session_instance

                with patch(
                    "fastapi_auth.services.rbac.UserRepository",
                    return_value=mock_user_repo,
                ):
                    with patch(
                        "fastapi_auth.services.rbac.RBACRepository",
                        return_value=mock_rbac_repo,
                    ):
                        result = await check_admin_from_request(request)

                        # Verify user was retrieved
                        assert result.email == user.email

                        # Verify SessionLocal was called exactly once (single session)
                        assert mock_db_session_instance.SessionLocal.call_count == 1

                        # Verify RBACRepository was instantiated with the session
                        # by checking that get_roles_by_user_id was called
                        mock_rbac_repo.get_roles_by_user_id.assert_called_once_with(
                            user.id
                        )

    @pytest.mark.asyncio
    async def test_check_role_from_request_uses_single_session(self, mock_settings):
        """Test check_role_from_request uses a single session for both user retrieval and RBAC check."""
        user = User(id=1, email="editor@example.com")
        editor_role = Role(id=1, name="editor")

        tz = ZoneInfo(mock_settings.timezone)
        payload = {
            "sub": user.email,
            "exp": datetime.datetime.now(tz=tz) + timedelta(minutes=30),
        }
        token = jwt.encode(
            payload, mock_settings.jwt_secret_key, algorithm=mock_settings.jwt_algorithm
        )

        request = MagicMock(spec=Request)
        request.headers.get.return_value = f"Bearer {token}"

        mock_session = AsyncMock()
        mock_user_repo = AsyncMock()
        mock_user_repo.get_user_by_email.return_value = user

        mock_rbac_repo = AsyncMock()
        mock_rbac_repo.get_roles_by_user_id.return_value = [editor_role]

        # Create async context manager mock
        async_context_manager = AsyncMock()
        async_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
        async_context_manager.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "fastapi_auth.services.rbac.get_settings", return_value=mock_settings
        ):
            with patch("fastapi_auth.services.rbac.DatabaseSession") as mock_db_session:
                mock_db_session_instance = MagicMock()
                mock_db_session_instance.SessionLocal = MagicMock(
                    return_value=async_context_manager
                )
                mock_db_session.return_value = mock_db_session_instance

                with patch(
                    "fastapi_auth.services.rbac.UserRepository",
                    return_value=mock_user_repo,
                ):
                    with patch(
                        "fastapi_auth.services.rbac.RBACRepository",
                        return_value=mock_rbac_repo,
                    ):
                        result = await check_role_from_request(request, "editor")

                        # Verify user was retrieved
                        assert result.email == user.email

                        # Verify SessionLocal was called exactly once (single session)
                        assert mock_db_session_instance.SessionLocal.call_count == 1

                        # Verify RBACRepository methods were called with the session
                        # get_roles_by_user_id should be called twice (once for admin check, once for role check)
                        assert mock_rbac_repo.get_roles_by_user_id.call_count == 2

    @pytest.mark.asyncio
    async def test_check_permissions_from_request_uses_single_session(
        self, mock_settings
    ):
        """Test check_permissions_from_request uses a single session for both user retrieval and RBAC check."""
        user = User(id=1, email="user@example.com")
        permission = Permission(id=1, name="read:users")

        tz = ZoneInfo(mock_settings.timezone)
        payload = {
            "sub": user.email,
            "exp": datetime.datetime.now(tz=tz) + timedelta(minutes=30),
        }
        token = jwt.encode(
            payload, mock_settings.jwt_secret_key, algorithm=mock_settings.jwt_algorithm
        )

        request = MagicMock(spec=Request)
        request.headers.get.return_value = f"Bearer {token}"

        mock_session = AsyncMock()
        mock_user_repo = AsyncMock()
        mock_user_repo.get_user_by_email.return_value = user

        mock_rbac_repo = AsyncMock()
        mock_rbac_repo.get_roles_by_user_id.return_value = []
        mock_rbac_repo.get_permissions_by_user_id.return_value = [permission]

        # Create async context manager mock
        async_context_manager = AsyncMock()
        async_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
        async_context_manager.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "fastapi_auth.services.rbac.get_settings", return_value=mock_settings
        ):
            with patch("fastapi_auth.services.rbac.DatabaseSession") as mock_db_session:
                mock_db_session_instance = MagicMock()
                mock_db_session_instance.SessionLocal = MagicMock(
                    return_value=async_context_manager
                )
                mock_db_session.return_value = mock_db_session_instance

                with patch(
                    "fastapi_auth.services.rbac.UserRepository",
                    return_value=mock_user_repo,
                ):
                    with patch(
                        "fastapi_auth.services.rbac.RBACRepository",
                        return_value=mock_rbac_repo,
                    ):
                        result = await check_permissions_from_request(
                            request, ["read:users"]
                        )

                        # Verify user was retrieved
                        assert result.email == user.email

                        # Verify SessionLocal was called exactly once (single session)
                        assert mock_db_session_instance.SessionLocal.call_count == 1

                        # Verify RBACRepository methods were called
                        mock_rbac_repo.get_roles_by_user_id.assert_called_once_with(
                            user.id
                        )
                        mock_rbac_repo.get_permissions_by_user_id.assert_called_once_with(
                            user.id
                        )
