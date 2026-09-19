from collections.abc import Iterator

from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session


class Base(DeclarativeBase):
    pass


def build_engine(url: str):
    return create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 5})


def get_session(request: Request) -> Iterator[Session]:
    with Session(request.app.state.engine) as session:
        yield session
