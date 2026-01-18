import httpx
from fastapi import Depends, HTTPException

from fastapi_auth.models.social_providers import SupportedProviders
from fastapi_auth.repositories.social_provider_repository import (
    SocialProviderRepository,
    get_social_provider_repository,
)
from fastapi_auth.repositories.user_repository import UserRepository
from fastapi_auth.schemas.user import UserJWTResponseSchema, UserSignupSchema
from fastapi_auth.utils.decorators.validators import validate_args
from fastapi_auth.utils.jwt import generate_jwt_token


class GithubSocialProvider:
    def __init__(
        self,
        social_repository: SocialProviderRepository,
        user_repository: UserRepository,
    ):
        self.repository = social_repository
        self.user_repository = user_repository

    async def _get_provider_settings(self):
        """Get provider settings from database. Always fetches fresh data."""
        return await self.repository.get_social_provider_by_type(
            type=SupportedProviders.GITHUB
        )

    async def exchange_code_for_token(self, code: str):
        # Make the request to the Github API to exchange the code for a token
        provider_settings = await self._get_provider_settings()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": provider_settings.client_id,
                    "client_secret": provider_settings.client_secret,
                    "code": code,
                },
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            return response.json()["access_token"]

    async def get_user_info(self, token: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-GitHub-Api-Version": "2022-11-28",
                    "Accept": "application/json",
                    "User-Agent": "app/oblox-fastapi-auth",
                },
            )
            response.raise_for_status()
            response_json = response.json()
            # GithubUserResponse is a Union type, try both models
            try:
                from fastapi_auth.schemas.social import GithubPublicUser

                return GithubPublicUser.model_validate(response_json)
            except Exception:
                from fastapi_auth.schemas.social import GithubPrivateUser

                return GithubPrivateUser.model_validate(response_json)

    @validate_args({"code": {"required": {"message": "Code is required."}}})
    async def _perform_login(self, code: str) -> UserJWTResponseSchema:
        provider_settings = await self._get_provider_settings()
        if not provider_settings:
            raise HTTPException(status_code=400, detail="Github is not configured.")
        token = await self.exchange_code_for_token(code=code)
        user_info = await self.get_user_info(token=token)
        user = await self.user_repository.create_user(
            user=UserSignupSchema(
                email=user_info.email,
                name=user_info.name,
                profile_pic=str(user_info.avatar_url) if user_info.avatar_url else None,
            )
        )

        return generate_jwt_token(user=user, settings=self.settings)

    async def login(self, **kwargs):
        code = kwargs.get("code", None)
        return await self._perform_login(code)


def get_github_social_provider(
    social_repository: Depends(get_social_provider_repository),
) -> GithubSocialProvider:
    return GithubSocialProvider(social_repository=social_repository)
