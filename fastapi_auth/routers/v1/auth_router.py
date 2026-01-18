from fastapi import APIRouter, Depends

from fastapi_auth.models.social_providers import SupportedProviders
from fastapi_auth.schemas.user import UserSignupSchema
from fastapi_auth.services.user_service import UserService, get_user_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup")
async def signup(
    payload: UserSignupSchema, user_service: UserService = Depends(get_user_service)
):
    return await user_service.signup_user(payload)


@router.post("/social/{provider_type}/login")
async def social_login(
    provider_type: SupportedProviders,
    payload: dict,
    user_service: UserService = Depends(get_user_service),
):
    return await user_service.social_login(provider_type, **payload)
