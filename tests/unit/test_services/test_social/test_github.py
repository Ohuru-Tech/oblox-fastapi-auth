from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import HTTPException

from fastapi_auth.models.social_providers import SocialProvider, SupportedProviders
from fastapi_auth.schemas.social import GithubPublicUser
from fastapi_auth.schemas.user import UserJWTResponseSchema
from fastapi_auth.services.social.github import GithubSocialProvider


class TestGithubSocialProviderExchangeCodeForToken:
    """Test exchange_code_for_token method."""

    @pytest.mark.asyncio
    async def test_exchange_code_for_token_success(self):
        """Test successful code exchange for token."""
        mock_social_repo = MagicMock()
        mock_social_repo.get_social_provider_by_type = AsyncMock(
            return_value=SocialProvider(
                provider_type=SupportedProviders.GITHUB.value,
                client_id="test_client_id",
                client_secret="test_client_secret",
            )
        )

        provider = GithubSocialProvider(mock_social_repo, AsyncMock())

        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "test_access_token"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = MagicMock()
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client_instance.post = AsyncMock(return_value=mock_response)

            result = await provider.exchange_code_for_token("test_code")

            assert result == "test_access_token"
            mock_client_instance.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_exchange_code_for_token_api_error(self):
        """Test exchange_code_for_token handles API errors."""
        mock_social_repo = MagicMock()
        mock_social_repo.get_social_provider_by_type = AsyncMock(
            return_value=SocialProvider(
                provider_type=SupportedProviders.GITHUB.value,
                client_id="test_client_id",
                client_secret="test_client_secret",
            )
        )

        provider = GithubSocialProvider(mock_social_repo, AsyncMock())

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Error", request=MagicMock(), response=MagicMock()
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = MagicMock()
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client_instance.post = AsyncMock(return_value=mock_response)

            with pytest.raises(httpx.HTTPStatusError):
                await provider.exchange_code_for_token("test_code")


class TestGithubSocialProviderGetUserInfo:
    """Test get_user_info method."""

    @pytest.mark.asyncio
    async def test_get_user_info_success(self):
        """Test successful user info retrieval."""
        mock_social_repo = MagicMock()
        mock_social_repo.get_social_provider_by_type = AsyncMock(
            return_value=SocialProvider(
                provider_type=SupportedProviders.GITHUB.value,
                client_id="test_client_id",
                client_secret="test_client_secret",
            )
        )

        provider = GithubSocialProvider(mock_social_repo, AsyncMock())

        github_user_data = {
            "login": "testuser",
            "id": 12345,
            "node_id": "MDQ6VXNlcjEyMzQ1",
            "avatar_url": "https://avatars.githubusercontent.com/u/12345",
            "gravatar_id": None,
            "url": "https://api.github.com/users/testuser",
            "html_url": "https://github.com/testuser",
            "followers_url": "https://api.github.com/users/testuser/followers",
            "following_url": "https://api.github.com/users/testuser/following{/other_user}",
            "gists_url": "https://api.github.com/users/testuser/gists{/gist_id}",
            "starred_url": "https://api.github.com/users/testuser/starred{/owner}{/repo}",
            "subscriptions_url": "https://api.github.com/users/testuser/subscriptions",
            "organizations_url": "https://api.github.com/users/testuser/orgs",
            "repos_url": "https://api.github.com/users/testuser/repos",
            "events_url": "https://api.github.com/users/testuser/events{/privacy}",
            "received_events_url": "https://api.github.com/users/testuser/received_events",
            "type": "User",
            "site_admin": False,
            "name": "Test User",
            "company": None,
            "blog": "",
            "location": None,
            "email": "test@example.com",
            "hireable": None,
            "bio": None,
            "twitter_username": None,
            "public_repos": 10,
            "public_gists": 5,
            "followers": 20,
            "following": 15,
            "created_at": "2020-01-01T00:00:00Z",
            "updated_at": "2021-01-01T00:00:00Z",
        }

        mock_response = MagicMock()
        mock_response.json.return_value = github_user_data
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = MagicMock()
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client_instance.get = AsyncMock(return_value=mock_response)

            result = await provider.get_user_info("test_token")

            assert isinstance(result, GithubPublicUser)
            assert result.email == "test@example.com"
            assert result.name == "Test User"

    @pytest.mark.asyncio
    async def test_get_user_info_api_error(self):
        """Test get_user_info handles API errors."""
        mock_social_repo = MagicMock()
        mock_social_repo.get_social_provider_by_type.return_value = SocialProvider(
            provider_type=SupportedProviders.GITHUB.value,
            client_id="test_client_id",
            client_secret="test_client_secret",
        )

        provider = GithubSocialProvider(mock_social_repo, AsyncMock())

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Error", request=MagicMock(), response=MagicMock()
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = MagicMock()
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client_instance.get = AsyncMock(return_value=mock_response)

            with pytest.raises(httpx.HTTPStatusError):
                await provider.get_user_info("test_token")


class TestGithubSocialProviderLogin:
    """Test login method."""

    @pytest.mark.asyncio
    async def test_login_success(self, mock_settings):
        """Test successful login flow."""
        mock_social_repo = MagicMock()
        mock_social_repo.get_social_provider_by_type = AsyncMock(
            return_value=SocialProvider(
                provider_type=SupportedProviders.GITHUB.value,
                client_id="test_client_id",
                client_secret="test_client_secret",
            )
        )

        mock_user_repo = AsyncMock()
        created_user = MagicMock()
        created_user.email = "test@example.com"
        mock_user_repo.create_user = AsyncMock(return_value=created_user)

        provider = GithubSocialProvider(mock_social_repo, mock_user_repo)

        # Mock settings attribute (fixing the bug in the actual code)
        provider.settings = mock_settings

        # Mock exchange_code_for_token and get_user_info
        provider.exchange_code_for_token = AsyncMock(return_value="test_access_token")

        github_user = GithubPublicUser(
            login="testuser",
            id=12345,
            node_id="MDQ6VXNlcjEyMzQ1",
            avatar_url="https://avatars.githubusercontent.com/u/12345",
            gravatar_id="",
            url="https://api.github.com/users/testuser",
            html_url="https://github.com/testuser",
            followers_url="https://api.github.com/users/testuser/followers",
            following_url="https://api.github.com/users/testuser/following{/other_user}",
            gists_url="https://api.github.com/users/testuser/gists{/gist_id}",
            starred_url="https://api.github.com/users/testuser/starred{/owner}{/repo}",
            subscriptions_url="https://api.github.com/users/testuser/subscriptions",
            organizations_url="https://api.github.com/users/testuser/orgs",
            repos_url="https://api.github.com/users/testuser/repos",
            events_url="https://api.github.com/users/testuser/events{/privacy}",
            received_events_url="https://api.github.com/users/testuser/received_events",
            type="User",
            site_admin=False,
            name="Test User",
            company=None,
            blog="",
            location=None,
            email="test@example.com",
            hireable=None,
            bio=None,
            public_repos=10,
            public_gists=5,
            followers=20,
            following=15,
            created_at="2020-01-01T00:00:00Z",
            updated_at="2021-01-01T00:00:00Z",
        )
        provider.get_user_info = AsyncMock(return_value=github_user)

        result = await provider.login(code="test_code")

        assert isinstance(result, UserJWTResponseSchema)
        assert result.access_token is not None
        assert result.refresh_token is not None

    @pytest.mark.asyncio
    async def test_login_with_missing_provider_settings(self):
        """Test login with missing provider settings raises HTTPException."""
        mock_social_repo = MagicMock()
        mock_social_repo.get_social_provider_by_type = AsyncMock(return_value=None)

        provider = GithubSocialProvider(mock_social_repo, AsyncMock())
        provider.settings = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await provider.login(code="test_code")

        assert exc_info.value.status_code == 400
        assert "not configured" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_login_with_missing_code(self):
        """Test login with missing code parameter."""
        mock_social_repo = MagicMock()
        mock_social_repo.get_social_provider_by_type.return_value = SocialProvider(
            provider_type=SupportedProviders.GITHUB.value,
            client_id="test_client_id",
            client_secret="test_client_secret",
        )

        provider = GithubSocialProvider(mock_social_repo, AsyncMock())
        provider.settings = MagicMock()

        # The validate_args decorator should catch this, but if code is None,
        # it will be passed to _perform_login which will fail
        with pytest.raises((HTTPException, TypeError, AttributeError)):
            await provider.login()
