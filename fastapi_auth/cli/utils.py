import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Coroutine, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
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
    """Print success message with Rich Panel and green styling."""
    panel = Panel(
        f"[green]✓[/green] {message}",
        border_style="green",
        title="[green]Success[/green]",
        title_align="left",
    )
    console.print(panel)


def print_error(message: str) -> None:
    """Print error message with Rich Panel and red styling."""
    panel = Panel(
        f"[red]✗[/red] {message}",
        border_style="red",
        title="[red]Error[/red]",
        title_align="left",
    )
    console.print(panel)


def print_info(message: str) -> None:
    """Print info message with Rich Panel and blue styling."""
    panel = Panel(
        f"[blue]ℹ[/blue] {message}",
        border_style="blue",
        title="[blue]Info[/blue]",
        title_align="left",
    )
    console.print(panel)


def print_table(
    title: str,
    rows: list[dict[str, Any]],
    column_names: Optional[list[str]] = None,
) -> None:
    """
    Print structured data using Rich Table.

    Args:
        title: Title for the table
        rows: List of dictionaries representing table rows
        column_names: Optional list of column names. If not provided, uses keys from first row.
    """
    table = Table(title=title, show_header=True, header_style="bold magenta")

    if not rows:
        console.print("[yellow]No data to display[/yellow]")
        return

    # Determine column names
    if column_names is None:
        column_names = list(rows[0].keys())

    # Add columns
    for col_name in column_names:
        table.add_column(col_name, style="cyan", no_wrap=False)

    # Add rows
    for row in rows:
        table.add_row(*[str(row.get(col, "")) for col in column_names])

    console.print(table)


def print_panel(
    content: str,
    title: Optional[str] = None,
    border_style: str = "white",
    title_style: Optional[str] = None,
) -> None:
    """
    Print formatted message using Rich Panel.

    Args:
        content: Content to display in the panel
        title: Optional title for the panel
        border_style: Style for the panel border (default: "white")
        title_style: Optional style for the title
    """
    title_text = title
    if title_style and title_text:
        title_text = f"[{title_style}]{title_text}[/{title_style}]"

    panel = Panel(
        content,
        border_style=border_style,
        title=title_text,
        title_align="left",
    )
    console.print(panel)
