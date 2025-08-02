from sqlmodel import SQLModel, create_engine, Session

sqlite_url = "sqlite:///backend.db"
engine = create_engine(sqlite_url, echo=False)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    with Session(engine) as session:
        yield session
