import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Coroutine

from rich.console import Console
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from fastapi_auth.database.db import get_engine

console = Console()


def get_async_session() -> async_sessionmaker:
    """Get async session maker for CLI context."""
    return async_sessionmaker(get_engine(), expire_on_commit=False)


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session context manager."""
    session_maker = get_async_session()
    async with session_maker() as session:
        yield session


def run_async(coro: Coroutine[Any, Any, Any]) -> Any:
    """Run async function in CLI context."""
    return asyncio.run(coro)


def print_success(message: str) -> None:
    """Print success message with Rich formatting."""
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str) -> None:
    """Print error message with Rich formatting."""
    console.print(f"[red]✗[/red] {message}")


def print_info(message: str) -> None:
    """Print info message with Rich formatting."""
    console.print(f"[blue]ℹ[/blue] {message}")
