import os
from pathlib import Path
from typing import Dict, Tuple

from sqlmodel import SQLModel, create_engine, Session, select

from backend.models import Heuristic

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HEURISTICS_PATH = DATA_DIR / "heuristics.yml"

ENV = os.getenv("APP_ENV", "dev")
DB_PATH = Path(f"data-{ENV}.db")
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)


def init_db() -> None:
    """Create tables if they don't exist."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    """Return a new DB session bound to the engine."""
    return Session(engine)


def _seed_from_yaml(session: Session) -> None:
    if session.exec(select(Heuristic)).first() is None and HEURISTICS_PATH.exists():
        import yaml

        data = yaml.safe_load(HEURISTICS_PATH.read_text()) or {}
        for label, pattern in data.items():
            row = Heuristic(user_id=0, label=label, pattern=pattern)
            session.add(row)
        session.commit()


def get_patterns() -> Dict[str, str]:
    """Return label->pattern mappings from the database."""
    init_db()
    with get_session() as session:
        _seed_from_yaml(session)
        rows = session.exec(select(Heuristic)).all()
        return {r.label: r.pattern for r in rows}


def add_pattern(label: str, pattern: str) -> None:
    """Store a new heuristic pattern in the database."""
    init_db()
    with get_session() as session:
        row = Heuristic(user_id=0, label=label, pattern=pattern)
        session.add(row)
        session.commit()


def get_user_and_global_patterns() -> Tuple[Dict[str, str], Dict[str, str]]:
    """Return separate mappings for user and global heuristics."""
    init_db()
    with get_session() as session:
        _seed_from_yaml(session)
        rows = session.exec(select(Heuristic)).all()
        user_patterns: Dict[str, str] = {}
        global_patterns: Dict[str, str] = {}
        for r in rows:
            if r.user_id == 0:
                global_patterns[r.label] = r.pattern
            else:
                user_patterns[r.label] = r.pattern
        return user_patterns, global_patterns
