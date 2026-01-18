from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_auth.database.db import get_session
from fastapi_auth.models import User
from fastapi_auth.models.rbac import Permission, Role


class RBACRepository:
    def __init__(self, database: AsyncSession):
        self.database = database

    async def get_role_by_name(self, name: str) -> Role | None:
        statement = select(Role).where(Role.name == name)
        result = await self.database.execute(statement=statement)
        return result.scalar_one_or_none()

    async def get_roles_by_user_id(self, user_id: int) -> list[Role]:
        statement = select(Role).join(Role.users).where(User.id == user_id)
        result = await self.database.execute(statement=statement)
        return result.scalars().all()

    async def get_roles_by_user_email(self, email: str) -> list[Role]:
        statement = select(Role).join(Role.users).where(User.email == email)
        result = await self.database.execute(statement=statement)
        return result.scalars().all()

    async def get_permissions_by_role_id(self, role_id: int) -> list[Permission]:
        statement = select(Permission).join(Permission.roles).where(Role.id == role_id)
        result = await self.database.execute(statement=statement)
        return result.scalars().all()

    async def get_permissions_by_user_id(self, user_id: int) -> list[Permission]:
        statement = (
            select(Permission)
            .join(Permission.roles)
            .join(Role.users)
            .where(User.id == user_id)
            .distinct()
        )
        result = await self.database.execute(statement=statement)
        return result.scalars().all()


def get_rbac_repository(
    database: AsyncSession = Depends(get_session),
) -> RBACRepository:
    return RBACRepository(database=database)
