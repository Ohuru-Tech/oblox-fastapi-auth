"""Tests for database module."""

from unittest.mock import Mock, patch

import pytest

from fastapi_auth.database.db import (
    DatabaseSession,
    _EngineProxy,
    get_engine,
    get_session,
)


class TestDatabaseModule:
    """Test database module functions."""

    def test_get_engine_creates_engine(self):
        """Test get_engine creates engine on first call."""
        # Reset global engine
        import fastapi_auth.database.db as db_module

        db_module._engine = None

        with patch("fastapi_auth.database.db.create_async_engine") as mock_create:
            mock_engine = Mock()
            mock_create.return_value = mock_engine

            engine = get_engine()
            assert engine is not None
            mock_create.assert_called_once()

    def test_get_engine_returns_cached_engine(self):
        """Test get_engine returns cached engine on subsequent calls."""
        import fastapi_auth.database.db as db_module

        db_module._engine = None

        with patch("fastapi_auth.database.db.create_async_engine") as mock_create:
            mock_engine = Mock()
            mock_create.return_value = mock_engine

            engine1 = get_engine()
            engine2 = get_engine()

            assert engine1 is engine2
            # Should only be called once
            assert mock_create.call_count == 1

    def test_engine_proxy_getattr(self):
        """Test _EngineProxy __getattr__ method."""
        proxy = _EngineProxy()

        with patch("fastapi_auth.database.db.get_engine") as mock_get:
            mock_engine = Mock()
            mock_engine.test_attr = "test_value"
            mock_get.return_value = mock_engine

            result = proxy.test_attr
            assert result == "test_value"
            mock_get.assert_called_once()

    def test_engine_proxy_call(self):
        """Test _EngineProxy __call__ method."""
        proxy = _EngineProxy()

        with patch("fastapi_auth.database.db.get_engine") as mock_get:
            mock_engine = Mock()
            # Make the engine callable
            mock_engine.return_value = mock_engine
            mock_get.return_value = mock_engine

            # _EngineProxy.__call__ calls get_engine()(*args, **kwargs)
            # So it calls the engine as a callable
            result = proxy()
            # The result is the return value of calling the engine
            assert result == mock_engine
            mock_get.assert_called_once()
            mock_engine.assert_called_once()

    @pytest.mark.asyncio
    async def test_database_session_get_session_success(self, mock_settings):
        """Test DatabaseSession.get_session yields session successfully."""
        with patch("fastapi_auth.database.db.get_engine") as mock_get_engine:
            mock_engine = Mock()
            mock_get_engine.return_value = mock_engine

            mock_session_maker = Mock()
            mock_session = Mock()

            # Create a proper async context manager
            class AsyncContextManager:
                async def __aenter__(self):
                    return mock_session

                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    return None

            mock_session_maker.return_value = AsyncContextManager()

            with patch(
                "fastapi_auth.database.db.async_sessionmaker",
                return_value=mock_session_maker,
            ):
                session_obj = DatabaseSession(mock_settings, fail_silently=False)

                async for session in session_obj.get_session():
                    assert session == mock_session

    @pytest.mark.asyncio
    async def test_database_session_get_session_error_fail_silently_false(
        self, mock_settings
    ):
        """Test DatabaseSession.get_session raises error when fail_silently=False."""
        with patch("fastapi_auth.database.db.get_engine") as mock_get_engine:
            mock_engine = Mock()
            mock_get_engine.return_value = mock_engine

            mock_session_maker = Mock()
            test_error = ValueError("Database connection failed")

            # Create a proper async context manager that raises on enter
            class AsyncContextManager:
                async def __aenter__(self):
                    raise test_error

                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    return None

            mock_session_maker.return_value = AsyncContextManager()

            with patch(
                "fastapi_auth.database.db.async_sessionmaker",
                return_value=mock_session_maker,
            ):
                session_obj = DatabaseSession(mock_settings, fail_silently=False)

                with pytest.raises(ValueError, match="Database connection failed"):
                    async for _ in session_obj.get_session():
                        pass

    @pytest.mark.asyncio
    async def test_database_session_get_session_error_fail_silently_true(
        self, mock_settings
    ):
        """Test DatabaseSession.get_session doesn't raise error when fail_silently=True."""
        with patch("fastapi_auth.database.db.get_engine") as mock_get_engine:
            mock_engine = Mock()
            mock_get_engine.return_value = mock_engine

            mock_session_maker = Mock()
            test_error = ValueError("Database connection failed")
            mock_context = Mock()
            mock_context.__aenter__ = Mock(side_effect=test_error)
            mock_session_maker.return_value = mock_context

            with patch(
                "fastapi_auth.database.db.async_sessionmaker",
                return_value=mock_session_maker,
            ):
                session_obj = DatabaseSession(mock_settings, fail_silently=True)

                # Should not raise exception
                try:
                    async for _ in session_obj.get_session():
                        pass
                except ValueError:
                    pytest.fail("Should not raise exception when fail_silently=True")

    def test_get_session_dependency(self):
        """Test get_session dependency function."""
        with patch("fastapi_auth.database.db.get_settings") as mock_get_settings:
            mock_settings = Mock()
            mock_get_settings.return_value = mock_settings

            with patch("fastapi_auth.database.db.DatabaseSession") as mock_db_session:
                result = get_session(mock_settings)

                # Should return async generator
                assert result is not None
                mock_db_session.assert_called_once_with(mock_settings)
