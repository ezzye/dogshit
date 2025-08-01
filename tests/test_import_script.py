import importlib
import runpy
from pathlib import Path

from sqlmodel import create_engine, Session, select

from backend.models import Heuristic


def test_import_script_loads_yaml(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    db_file = tmp_path / "rules.db"

    from bankcleanr.rules import db_store

    importlib.reload(db_store)
    db_store.DB_PATH = db_file
    db_store.engine = create_engine(f"sqlite:///{db_file}", echo=False)
    db_store.init_db()

    root = Path(__file__).resolve().parents[1]
    runpy.run_path(str(root / "scripts" / "import_heuristics.py"), run_name="__main__")

    with Session(db_store.engine) as session:
        labels = [h.label for h in session.exec(select(Heuristic)).all()]

    assert "spotify" in labels
