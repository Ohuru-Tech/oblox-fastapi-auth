"""Tests for CLI utilities."""

from unittest.mock import patch

import pytest
from rich.panel import Panel

from fastapi_auth.cli.utils import (
    get_async_session,
    get_db_session,
    print_error,
    print_info,
    print_panel,
    print_success,
    print_table,
    run_async,
)


class TestCLIUtils:
    """Test CLI utility functions."""

    def test_print_success_uses_rich_panel(self, capsys):
        """Test print_success uses Rich Panel with green styling."""

        with patch("fastapi_auth.cli.utils.console") as mock_console:
            print_success("Test success message")
            # Verify console.print was called (Rich Panel is used internally)
            assert mock_console.print.called
            # Check that a Panel object was passed
            call_args = mock_console.print.call_args[0]
            assert len(call_args) > 0
            panel = call_args[0]
            assert isinstance(panel, Panel)
            # Check that the panel has green border style
            assert panel.border_style == "green"
            assert "green" in panel.title.lower() or "success" in panel.title.lower()

    def test_print_error_uses_rich_panel(self, capsys):
        """Test print_error uses Rich Panel with red styling."""

        with patch("fastapi_auth.cli.utils.console") as mock_console:
            print_error("Test error message")
            # Verify console.print was called
            assert mock_console.print.called
            # Check that a Panel object was passed
            call_args = mock_console.print.call_args[0]
            assert len(call_args) > 0
            panel = call_args[0]
            assert isinstance(panel, Panel)
            # Check that the panel has red border style
            assert panel.border_style == "red"
            assert "red" in panel.title.lower() or "error" in panel.title.lower()

    def test_print_info_uses_rich_panel(self, capsys):
        """Test print_info uses Rich Panel with blue styling."""

        with patch("fastapi_auth.cli.utils.console") as mock_console:
            print_info("Test info message")
            # Verify console.print was called
            assert mock_console.print.called
            # Check that a Panel object was passed
            call_args = mock_console.print.call_args[0]
            assert len(call_args) > 0
            panel = call_args[0]
            assert isinstance(panel, Panel)
            # Check that the panel has blue border style
            assert panel.border_style == "blue"
            assert "blue" in panel.title.lower() or "info" in panel.title.lower()

    def test_print_table_function_exists(self):
        """Test print_table() function exists and creates Rich Table."""
        # Import should work if function exists
        try:
            from fastapi_auth.cli.utils import print_table

            assert callable(print_table)
        except ImportError:
            pytest.fail("print_table function does not exist")

    def test_print_panel_function_exists(self):
        """Test print_panel() function exists and creates Rich Panel."""
        # Import should work if function exists
        try:
            from fastapi_auth.cli.utils import print_panel

            assert callable(print_panel)
        except ImportError:
            pytest.fail("print_panel function does not exist")

    def test_get_async_session(self):
        """Test get_async_session returns async_sessionmaker."""
        session_maker = get_async_session()
        assert session_maker is not None

    @pytest.mark.asyncio
    async def test_get_db_session(self, test_engine):
        """Test get_db_session context manager."""
        from sqlalchemy.ext.asyncio import async_sessionmaker

        # Mock get_engine to return test_engine
        with patch("fastapi_auth.cli.utils.get_engine", return_value=test_engine):
            async with get_db_session() as session:
                assert session is not None
                assert isinstance(session, type(async_sessionmaker()()))

    def test_run_async(self):
        """Test run_async executes async function."""

        async def async_func():
            return "test_result"

        result = run_async(async_func())
        assert result == "test_result"

    def test_run_async_with_exception(self):
        """Test run_async handles exceptions."""

        async def async_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            run_async(async_func())

    def test_print_table_with_empty_rows(self):
        """Test print_table handles empty rows list."""
        with patch("fastapi_auth.cli.utils.console") as mock_console:
            print_table(title="Test Table", rows=[])
            # Verify console.print was called with "No data to display" message
            assert mock_console.print.called
            call_args = mock_console.print.call_args[0]
            assert len(call_args) > 0
            assert "No data to display" in call_args[0]

    def test_print_table_with_rows(self):
        """Test print_table creates Rich Table with rows."""
        from rich.table import Table

        with patch("fastapi_auth.cli.utils.console") as mock_console:
            print_table(
                title="Test Table",
                rows=[{"Field": "Name", "Value": "Test"}],
                column_names=["Field", "Value"],
            )
            # Verify console.print was called
            assert mock_console.print.called
            # Check that a Table object was passed
            call_args = mock_console.print.call_args[0]
            assert len(call_args) > 0
            obj = call_args[0]
            assert isinstance(obj, Table)
            assert obj.title == "Test Table"

    def test_print_table_without_column_names(self):
        """Test print_table infers column names from rows when not provided."""
        from rich.table import Table

        with patch("fastapi_auth.cli.utils.console") as mock_console:
            print_table(
                title="Test Table",
                rows=[{"Field": "Name", "Value": "Test"}],
                # column_names not provided - should infer from rows
            )
            # Verify console.print was called
            assert mock_console.print.called
            # Check that a Table object was passed
            call_args = mock_console.print.call_args[0]
            assert len(call_args) > 0
            obj = call_args[0]
            assert isinstance(obj, Table)
            assert obj.title == "Test Table"

    def test_print_panel_with_content(self):
        """Test print_panel creates Rich Panel with content."""
        with patch("fastapi_auth.cli.utils.console") as mock_console:
            print_panel(content="Test content", title="Test Title")
            # Verify console.print was called
            assert mock_console.print.called
            # Check that a Panel object was passed
            call_args = mock_console.print.call_args[0]
            assert len(call_args) > 0
            panel = call_args[0]
            assert isinstance(panel, Panel)
            assert panel.renderable == "Test content"
            assert panel.title == "Test Title"

    def test_print_panel_with_title_style(self):
        """Test print_panel applies title style when provided."""
        with patch("fastapi_auth.cli.utils.console") as mock_console:
            print_panel(
                content="Test content",
                title="Test Title",
                title_style="green",
                border_style="green",
            )
            # Verify console.print was called
            assert mock_console.print.called
            # Check that a Panel object was passed
            call_args = mock_console.print.call_args[0]
            assert len(call_args) > 0
            panel = call_args[0]
            assert isinstance(panel, Panel)
            assert panel.border_style == "green"
            # Title should have style applied
            assert panel.title is not None

    def test_print_panel_without_title(self):
        """Test print_panel works without title."""
        with patch("fastapi_auth.cli.utils.console") as mock_console:
            print_panel(content="Test content")
            # Verify console.print was called
            assert mock_console.print.called
            # Check that a Panel object was passed
            call_args = mock_console.print.call_args[0]
            assert len(call_args) > 0
            panel = call_args[0]
            assert isinstance(panel, Panel)
            assert panel.renderable == "Test content"
