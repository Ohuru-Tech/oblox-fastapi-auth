import datetime
from datetime import timedelta
from zoneinfo import ZoneInfo

import jwt
from fastapi import HTTPException

from fastapi_auth.models.user import User
from fastapi_auth.schemas.user import UserJWTResponseSchema
from fastapi_auth.settings import Settings


def generate_jwt_token(user: User, settings: Settings) -> UserJWTResponseSchema:
    tz = ZoneInfo(settings.timezone)
    payload = {
        "iss": settings.project_name,
        "sub": user.email,
        "aud": settings.jwt_audience,
        "exp": datetime.datetime.now(tz=tz)
        + timedelta(minutes=settings.jwt_access_token_expire_minutes),
    }
    access_token = jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    payload.update(
        {
            "exp": datetime.datetime.now(tz=tz)
            + timedelta(minutes=settings.jwt_refresh_token_expire_minutes),
        }
    )
    refresh_token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return UserJWTResponseSchema(access_token=access_token, refresh_token=refresh_token)


def verify_jwt_token(token: str, settings: Settings) -> User:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
        )
        return User(email=payload["sub"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
