import enum

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from fastapi_auth.models.base import Base
from fastapi_auth.models.common import EncryptedString, create_enum_column


class SupportedProviders(enum.Enum):
    GITHUB = "github"


class SocialProvider(Base):
    __tablename__ = "social_providers"

    provider_type: Mapped[str] = mapped_column(
        create_enum_column(SupportedProviders, name="social_provider_type"),
        nullable=False,
    )
    client_id: Mapped[str] = mapped_column(String, nullable=False)
    client_secret: Mapped[str] = mapped_column(EncryptedString, nullable=False)
