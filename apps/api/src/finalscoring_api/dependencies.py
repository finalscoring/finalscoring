from collections.abc import Generator

from sqlalchemy.orm import Session

from finalscoring.db.session import create_session_factory
from finalscoring_api.config import settings

# Pre-create the session factory once during application startup
_session_factory = create_session_factory(settings.database_url)


def get_db() -> Generator[Session, None, None]:
    """Dependency to provide a database session for each request."""
    session = _session_factory()
    try:
        yield session
    finally:
        session.close()
