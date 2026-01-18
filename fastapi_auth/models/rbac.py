from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fastapi_auth.models.base import Base


class Role(Base):
    __tablename__ = "auth_roles"

    name: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    users: Mapped[list["User"]] = relationship(  # pyright: ignore[reportUndefinedVariable]  # noqa: F821
        "User",
        secondary="auth_user_roles",
        back_populates="roles",
    )
    permissions: Mapped[list["Permission"]] = relationship(
        "Permission",
        secondary="auth_role_permissions",
        back_populates="roles",
    )


class UserRole(Base):
    __tablename__ = "auth_user_roles"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("auth_users.id"), primary_key=True
    )
    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("auth_roles.id"), primary_key=True
    )
    # Override id to be part of composite primary key but still autoincrement
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)


class Permission(Base):
    __tablename__ = "auth_permissions"

    name: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    resource: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    roles: Mapped[list["Role"]] = relationship(
        "Role",
        secondary="auth_role_permissions",
        back_populates="permissions",
    )


class RolePermission(Base):
    __tablename__ = "auth_role_permissions"

    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("auth_roles.id"), primary_key=True
    )
    permission_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("auth_permissions.id"), primary_key=True
    )
    # Override id to be part of composite primary key but still autoincrement
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
