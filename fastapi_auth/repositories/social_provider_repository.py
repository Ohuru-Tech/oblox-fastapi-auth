from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_auth.database.db import get_session
from fastapi_auth.models.social_providers import SocialProvider, SupportedProviders


class SocialProviderRepository:
    def __init__(self, database: AsyncSession):
        self.database = database

    async def get_social_provider_by_type(
        self, type: SupportedProviders
    ) -> SocialProvider | None:
        statement = select(SocialProvider).where(
            SocialProvider.provider_type == type.value
        )
        result = await self.database.execute(statement=statement)
        return result.scalar_one_or_none()


def get_social_provider_repository(
    database: Depends(get_session),
) -> SocialProviderRepository:
    return SocialProviderRepository(database=database)
