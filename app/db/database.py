from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Session,
    sessionmaker,
)

from app.config import settings


class Base(DeclarativeBase):
    pass


# ========================================
# Engine settings
# ========================================

engine_kwargs = {}

if settings.database_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {
        "check_same_thread": False,
    }


engine = create_engine(
    settings.database_url,
    **engine_kwargs,
)


# ========================================
# SQLite foreign key enforcement
# ========================================

if settings.database_url.startswith("sqlite"):

    @event.listens_for(
        engine,
        "connect",
    )
    def set_sqlite_pragma(
        dbapi_connection,
        connection_record,
    ):
        cursor = dbapi_connection.cursor()

        try:
            cursor.execute(
                "PRAGMA foreign_keys=ON"
            )
        finally:
            cursor.close()


# ========================================
# Session
# ========================================

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


# ========================================
# Database dependency
# ========================================

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()