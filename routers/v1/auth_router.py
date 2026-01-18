from fastapi import APIRouter, Depends

from models.social_providers import SupportedProviders
from schemas.user import UserSignupSchema
from services.user_service import UserService, get_user_service

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
