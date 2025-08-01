#!/usr/bin/env python3
"""Seed the heuristics database from the default YAML file."""

from bankcleanr.rules import db_store
from backend.models import Heuristic
import yaml


def main() -> None:
    """Load patterns from heuristics.yml into the database."""
    db_store.init_db()
    data = yaml.safe_load(db_store.HEURISTICS_PATH.read_text()) or {}
    with db_store.get_session() as session:
        for label, pattern in data.items():
            row = Heuristic(user_id=0, label=label, pattern=pattern)
            session.add(row)
        session.commit()
    print(f"Imported {len(data)} heuristics")


if __name__ == "__main__":
    main()
