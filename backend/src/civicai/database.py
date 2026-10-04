from collections.abc import Iterator
import os

from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session


class Base(DeclarativeBase):
    pass


def build_engine(url: str):
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_size=int(os.environ.get("DB_POOL_SIZE", "5")),
        max_overflow=int(os.environ.get("DB_MAX_OVERFLOW", "5")),
        pool_timeout=int(os.environ.get("DB_POOL_TIMEOUT_SECONDS", "10")),
        pool_recycle=int(os.environ.get("DB_POOL_RECYCLE_SECONDS", "300")),
        connect_args={"connect_timeout": 5},
    )


def get_session(request: Request) -> Iterator[Session]:
    with Session(request.app.state.engine) as session:
        yield session
