from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Dict, Callable

import yaml

from .transaction import Transaction, normalise
from .llm import classify_transactions

DATA_DIR = Path(__file__).resolve().parent / "data"
KB_PATH = DATA_DIR / "cancellation.yml"


@dataclass
class Recommendation:
    transaction: Transaction
    category: str
    action: str
    info: Dict[str, str] | None = None
    reasons: List[str] | None = None
    checklist: List[str] | None = None


def load_knowledge_base(path: Path = KB_PATH) -> Dict[str, Dict[str, str]]:
    """Load the cancellation knowledge-base."""
    if path.exists():
        return yaml.safe_load(path.read_text()) or {}
    return {}


def recommend_transactions(
    transactions: Iterable,
    provider: str | None = None,
    kb_path: Path = KB_PATH,
    confirm: Callable[[str], str] | None = None,
) -> List[Recommendation]:
    """Return recommendations for each transaction."""
    txs = [normalise(tx) for tx in transactions]
    labels = classify_transactions(txs, provider=provider, confirm=confirm)
    kb = load_knowledge_base(kb_path)
    results: List[Recommendation] = []
    for tx, label in zip(txs, labels):
        if label in kb:
            action = "Cancel"
            details = kb[label]
            info = {
                k: v
                for k, v in details.items()
                if k in {"url", "email", "phone"} and v
            }
        elif label == "unknown":
            action = "Investigate"
            info = None
        else:
            action = "Keep"
            info = None
        results.append(Recommendation(tx, label, action, info))
    return results
