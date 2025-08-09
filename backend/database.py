from collections.abc import Generator

from sqlmodel import SQLModel, create_engine, Session

sqlite_url = "sqlite:///backend.db"
engine = create_engine(sqlite_url, echo=False)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
