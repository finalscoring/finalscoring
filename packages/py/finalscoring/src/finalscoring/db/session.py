from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


def create_session_factory(database_url: str) -> sessionmaker[Session]:
    engine = create_engine(database_url, future=True)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db_session(database_url: str) -> Generator[Session, None, None]:
    session_factory = create_session_factory(database_url)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
