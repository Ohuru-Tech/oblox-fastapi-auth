from typing import Optional

from pydantic import BaseModel


class UserPasswordLoginSchema(BaseModel):
    email: str
    password: Optional[str] = None


class UserSignupSchema(BaseModel):
    email: str
    password: Optional[str] = None
    name: Optional[str] = None
    profile_pic: Optional[str] = None


class UserJWTResponseSchema(BaseModel):
    access_token: str
    refresh_token: str


class UserSocialLoginSchema(BaseModel):
    provider: str
    access_token: Optional[str] = None
    code: Optional[str] = None


class UserSignupResponseSchema(BaseModel):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    message: str
