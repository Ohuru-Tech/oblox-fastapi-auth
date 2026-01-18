from fastapi import Depends, HTTPException

from fastapi_auth.models.social_providers import SupportedProviders
from fastapi_auth.repositories.user_repository import (
    UserRepository,
    get_user_repository,
)
from fastapi_auth.schemas.user import (
    UserJWTResponseSchema,
    UserPasswordLoginSchema,
    UserSignupResponseSchema,
    UserSignupSchema,
)
from fastapi_auth.services.social import provider_maps
from fastapi_auth.settings import Settings, get_settings
from fastapi_auth.utils.jwt import generate_jwt_token
from fastapi_auth.utils.password import verify_password


class UserService:
    def __init__(self, repository: UserRepository, settings: Settings):
        self.repository = repository
        self.settings = settings

    async def social_login(self, provider_type: SupportedProviders, **kwargs):
        from fastapi_auth.repositories.social_provider_repository import (
            SocialProviderRepository,
        )

        provider_class = provider_maps[provider_type]
        # Instantiate the provider with required dependencies
        social_repo = SocialProviderRepository(self.repository.database)
        provider = provider_class(social_repo, self.repository)
        # Set settings on provider - GithubSocialProvider needs this for JWT generation
        if hasattr(provider, "settings"):
            provider.settings = self.settings
        return await provider.login(**kwargs)

    async def log_user_in(
        self, user_login: UserPasswordLoginSchema
    ) -> UserJWTResponseSchema:
        user = await self.repository.get_user_by_email(email=user_login.email)

        # If the user deos not exist, raise an exception
        if not user:
            raise HTTPException(
                status_code=404, detail="No user exists with the given email."
            )

        # See if this is a passwordless login
        if self.settings.passwordless_login_enabled:
            await self.signup_user(user_signup=UserSignupSchema(email=user_login.email))

        if not user.password:
            raise HTTPException(status_code=400, detail="Password is required.")

        # Verify the password
        if not verify_password(
            password=user_login.password, hashed_password=user.password
        ):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Generate a jwt for the user and return
        return generate_jwt_token(user=user, settings=self.settings)

    async def signup_user(
        self, user_signup: UserSignupSchema
    ) -> UserSignupResponseSchema:
        # Passwordless flows should not be using signup route
        if self.settings.passwordless_login_enabled:
            raise HTTPException(
                status_code=400, detail="Passwordless signup is not supported."
            )

        user = await self.repository.get_user_by_email(email=user_signup.email)

        # If a user exists, raise an exception
        if user:
            raise HTTPException(status_code=400, detail="User already exists.")

        # If email verification is required, send a verification email
        if self.settings.email_verification_required:
            return UserSignupResponseSchema(
                message="OTP sent to email for verification."
            )

        # Create the user
        created_user = await self.repository.create_user(user=user_signup)

        # Generate a jwt for the user and return
        return generate_jwt_token(user=created_user, settings=self.settings)


def get_user_service(
    repository: UserRepository = Depends(get_user_repository),
    settings: Settings = Depends(get_settings),
) -> UserService:
    return UserService(repository=repository, settings=settings)
