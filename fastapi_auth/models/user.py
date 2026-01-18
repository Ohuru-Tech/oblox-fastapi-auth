from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fastapi_auth.models.base import Base


class User(Base):
    __tablename__ = "auth_users"

    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    profile_pic: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password: Mapped[str | None] = mapped_column(String(255), nullable=True)

    roles: Mapped[list["Role"]] = relationship(  # pyright: ignore[reportUndefinedVariable]  # noqa: F821
        "Role", secondary="auth_user_roles", back_populates="users"
    )
    is_staff: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
