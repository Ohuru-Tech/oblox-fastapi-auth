from pydantic import BaseModel


class UserPasswordLoginSchema(BaseModel):
    email: str
    password: str | None


class UserSignupSchema(BaseModel):
    email: str
    password: str | None
    name: str | None
    profile_pic: str | None


class UserJWTResponseSchema(BaseModel):
    access_token: str
    refresh_token: str


class UserSocialLoginSchema(BaseModel):
    provider: str
    access_token: str | None
    code: str | None


class UserSignupResponseSchema(BaseModel):
    access_token: str | None
    refresh_token: str | None
    message: str
