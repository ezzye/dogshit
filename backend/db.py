from sqlmodel import SQLModel, create_engine, Session
import os
from pathlib import Path

ENV = os.getenv("APP_ENV", "dev")
DB_PATH = Path(f"data-{ENV}.db")
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)
