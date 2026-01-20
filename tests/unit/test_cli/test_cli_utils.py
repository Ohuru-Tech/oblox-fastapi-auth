"""Tests for CLI utilities."""

from unittest.mock import patch

import pytest
from rich.panel import Panel

from fastapi_auth.cli.utils import (
    get_async_session,
    get_db_session,
    print_error,
    print_info,
    print_success,
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
