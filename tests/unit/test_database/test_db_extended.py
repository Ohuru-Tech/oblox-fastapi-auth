"""Extended database tests to cover missing lines."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from fastapi_auth.database.db import DatabaseSession


class TestDatabaseExtended:
    """Extended database tests."""

    @pytest.mark.asyncio
    async def test_database_session_get_session_exception_path(self, mock_settings):
        """Test DatabaseSession.get_session exception handling path (line 50)."""
        with patch("fastapi_auth.database.db.get_engine") as mock_get_engine:
            mock_engine = Mock()
            mock_get_engine.return_value = mock_engine

            mock_session_maker = Mock()
            test_error = ValueError("Database connection failed")
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(side_effect=test_error)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_session_maker.return_value = mock_context

            with patch(
                "fastapi_auth.database.db.async_sessionmaker",
                return_value=mock_session_maker,
            ):
                session_obj = DatabaseSession(mock_settings, fail_silently=True)

                # Should not raise when fail_silently=True
                async for _ in session_obj.get_session():
                    pass  # Should complete without raising

                # Test fail_silently=False
                session_obj2 = DatabaseSession(mock_settings, fail_silently=False)
                with pytest.raises(ValueError, match="Database connection failed"):
                    async for _ in session_obj2.get_session():
                        pass
