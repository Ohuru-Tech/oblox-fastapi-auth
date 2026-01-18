import datetime
from datetime import timedelta
from zoneinfo import ZoneInfo

import jwt
import pytest
from fastapi import HTTPException

from fastapi_auth.models.user import User
from fastapi_auth.settings import Settings
from fastapi_auth.utils.jwt import generate_jwt_token, verify_jwt_token


class TestGenerateJWTToken:
    """Test JWT token generation."""

    def test_generate_jwt_token_creates_valid_tokens(self, mock_settings):
        """Test that generate_jwt_token creates valid JWT tokens."""
        user = User(email="test@example.com")
        result = generate_jwt_token(user, mock_settings)

        assert result.access_token is not None
        assert result.refresh_token is not None
        assert isinstance(result.access_token, str)
        assert isinstance(result.refresh_token, str)

    def test_generate_jwt_token_has_correct_payload_structure(self, mock_settings):
        """Test that generated tokens have correct payload structure."""
        user = User(email="test@example.com")
        result = generate_jwt_token(user, mock_settings)

        # Decode access token
        access_payload = jwt.decode(
            result.access_token,
            mock_settings.jwt_secret_key,
            algorithms=[mock_settings.jwt_algorithm],
            audience=mock_settings.jwt_audience,
        )

        assert access_payload["iss"] == mock_settings.project_name
        assert access_payload["sub"] == user.email
        assert access_payload["aud"] == mock_settings.jwt_audience
        assert "exp" in access_payload

    def test_generate_jwt_token_different_expiration_times(self, mock_settings):
        """Test that access and refresh tokens have different expiration times."""
        user = User(email="test@example.com")
        result = generate_jwt_token(user, mock_settings)

        # Decode both tokens
        access_payload = jwt.decode(
            result.access_token,
            mock_settings.jwt_secret_key,
            algorithms=[mock_settings.jwt_algorithm],
            audience=mock_settings.jwt_audience,
            options={"verify_exp": False},
        )

        refresh_payload = jwt.decode(
            result.refresh_token,
            mock_settings.jwt_secret_key,
            algorithms=[mock_settings.jwt_algorithm],
            audience=mock_settings.jwt_audience,
            options={"verify_exp": False},
        )

        # Refresh token should expire later than access token
        assert refresh_payload["exp"] > access_payload["exp"]

        # Check expiration times match settings
        tz = ZoneInfo(mock_settings.timezone)
        now = datetime.datetime.now(tz=tz)
        expected_access_exp = now + timedelta(
            minutes=mock_settings.jwt_access_token_expire_minutes
        )
        expected_refresh_exp = now + timedelta(
            minutes=mock_settings.jwt_refresh_token_expire_minutes
        )

        # Allow 1 second tolerance
        assert abs(access_payload["exp"] - expected_access_exp.timestamp()) < 1
        assert abs(refresh_payload["exp"] - expected_refresh_exp.timestamp()) < 1


class TestVerifyJWTToken:
    """Test JWT token verification."""

    def test_verify_jwt_token_with_valid_token(self, mock_settings):
        """Test verify_jwt_token with valid token."""
        user = User(email="test@example.com")
        token_data = generate_jwt_token(user, mock_settings)

        verified_user = verify_jwt_token(token_data.access_token, mock_settings)

        assert verified_user.email == user.email

    def test_verify_jwt_token_with_expired_token(self, mock_settings):
        """Test verify_jwt_token with expired token."""
        # Create an expired token
        tz = ZoneInfo(mock_settings.timezone)
        expired_payload = {
            "iss": mock_settings.project_name,
            "sub": "test@example.com",
            "aud": mock_settings.jwt_audience,
            "exp": datetime.datetime.now(tz=tz) - timedelta(hours=1),
        }
        expired_token = jwt.encode(
            expired_payload,
            mock_settings.jwt_secret_key,
            algorithm=mock_settings.jwt_algorithm,
        )

        with pytest.raises(HTTPException) as exc_info:
            verify_jwt_token(expired_token, mock_settings)

        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    def test_verify_jwt_token_with_invalid_token(self, mock_settings):
        """Test verify_jwt_token with invalid token."""
        invalid_token = "invalid.token.here"

        with pytest.raises(HTTPException) as exc_info:
            verify_jwt_token(invalid_token, mock_settings)

        assert exc_info.value.status_code == 401
        assert "invalid" in exc_info.value.detail.lower()

    def test_verify_jwt_token_with_wrong_secret(self, mock_settings):
        """Test verify_jwt_token with token signed with wrong secret."""
        user = User(email="test@example.com")
        token_data = generate_jwt_token(user, mock_settings)

        # Create settings with different secret
        wrong_settings = Settings(
            database_url="sqlite+aiosqlite:///:memory:",
            jwt_secret_key="wrong-secret-key",
            jwt_algorithm=mock_settings.jwt_algorithm,
        )

        with pytest.raises(HTTPException) as exc_info:
            verify_jwt_token(token_data.access_token, wrong_settings)

        assert exc_info.value.status_code == 401
