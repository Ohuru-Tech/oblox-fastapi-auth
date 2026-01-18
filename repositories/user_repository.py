from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_session
from models.user import User
from schemas.user import UserSignupSchema


class UserRepository:
    def __init__(self, database: AsyncSession):
        self.database = database

    async def create_user(self, user: UserSignupSchema):
        async with self.database.begin():
            self.database.add(
                User(
                    email=user.email,
                    name=user.name,
                    profile_pic=user.profile_pic,
                    password=user.password,
                )
            )
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
