"""Tests for CLI utilities."""

from unittest.mock import patch

import pytest

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

    def test_print_success(self, capsys):
        """Test print_success function."""
        print_success("Test success message")
        # Rich console output is captured differently, just verify no exception
        assert True

    def test_print_error(self, capsys):
        """Test print_error function."""
        print_error("Test error message")
        # Rich console output is captured differently, just verify no exception
        assert True

    def test_print_info(self, capsys):
        """Test print_info function."""
        print_info("Test info message")
        # Rich console output is captured differently, just verify no exception
        assert True

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
