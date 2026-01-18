from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_auth.database.db import get_session
from fastapi_auth.models.user import User
from fastapi_auth.schemas.user import UserSignupSchema


class UserRepository:
    def __init__(self, database: AsyncSession):
        self.database = database

    async def create_user(self, user: UserSignupSchema):
        new_user = User(
            email=user.email,
            name=user.name,
            profile_pic=user.profile_pic,
            password=user.password,
        )
        self.database.add(new_user)
        await self.database.commit()
        await self.database.refresh(new_user)
        return await self.get_user_by_email(email=user.email)

    async def get_user_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        result = await self.database.execute(statement=statement)
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> User | None:
        statement = select(User).where(User.id == user_id)
        result = await self.database.execute(statement=statement)
        return result.scalar_one_or_none()


def get_user_repository(
    database: AsyncSession = Depends(get_session),
) -> UserRepository:
    return UserRepository(database=database)
