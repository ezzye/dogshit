"""Manage heuristic classification and persistence."""

from __future__ import annotations

from typing import Iterable, List, Dict
import json
import os
import sys
import urllib.request

from bankcleanr.transaction import Transaction
from . import regex


class Manager:
    """Handle heuristic classification and learning."""

    def __init__(self) -> None:
        self.pending: Dict[str, str] = {}

    def classify(self, transactions: Iterable[Transaction]) -> List[str]:
        """Classify transactions using existing regex patterns."""
        labels: List[str] = []
        for tx in transactions:
            labels.append(regex.classify(tx.description))
        return labels

    def merge_llm_rules(
        self, transactions: Iterable[Transaction], labels: Iterable[str]
    ) -> None:
        """Record LLM-suggested rules for unknown transactions."""
        for tx, label in zip(transactions, labels):
            if label != "unknown" and regex.classify(tx.description) == "unknown":
                self.pending[label] = tx.description

    def persist(self) -> None:
        """Persist pending rules and reload patterns."""
        if not self.pending:
            return
        backend_url = os.getenv("BANKCLEANR_BACKEND_URL")
        token = os.getenv("BANKCLEANR_BACKEND_TOKEN")
        for label, pattern in self.pending.items():
            regex.add_pattern(label, pattern)
            if backend_url and token:
                dest = f"{backend_url.rstrip('/')}/heuristics?token={token}"
                payload = json.dumps({"label": label, "pattern": pattern}).encode()
                try:
                    req = urllib.request.Request(
                        dest,
                        data=payload,
                        method="POST",
                        headers={"Content-Type": "application/json"},
                    )
                    urllib.request.urlopen(req, timeout=5)
                except Exception as exc:  # pragma: no cover - ignore network errors
                    print(f"Failed to POST heuristic: {exc}", file=sys.stderr)
        regex.reload_patterns()
        self.pending.clear()
