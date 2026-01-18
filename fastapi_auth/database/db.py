import traceback

from fastapi.param_functions import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio.engine import create_async_engine
from sqlalchemy.ext.asyncio.session import async_sessionmaker

from fastapi_auth.settings import Settings, get_settings
from fastapi_auth.utils.logging import get_logger

logger = get_logger(__name__)

# Engine will be initialized lazily when first accessed
_engine = None


def get_engine():
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(settings.database_url, echo=False)
    return _engine


# Module-level engine for backward compatibility
# This will be initialized on first access via get_engine()
class _EngineProxy:
    """Proxy class to lazily initialize engine."""

    def __getattr__(self, name):
        return getattr(get_engine(), name)

    def __call__(self, *args, **kwargs):
        return get_engine()(*args, **kwargs)


engine = _EngineProxy()


class DatabaseSession:
    def __init__(self, config: Settings, fail_silently: bool = False):
        self.config = config
        self.fail_silently = fail_silently
        self.SessionLocal = async_sessionmaker(get_engine(), expire_on_commit=False)

    async def get_session(self):
        try:
            async with self.SessionLocal() as session:
                yield session
        except Exception as e:
            logger.error(f"Failed to get database session: {e}")
            logger.error(traceback.format_exc())
            if not self.fail_silently:
                raise e


def get_session(settings: Settings = Depends(get_settings)) -> AsyncSession:
    return DatabaseSession(settings).get_session()
