"""Adapter for a locally running Ollama server."""

from __future__ import annotations

from typing import Dict, Iterable, List
from pathlib import Path
import requests

from .base import AbstractAdapter
from .utils import load_heuristics_texts
from bankcleanr.transaction import normalise
from bankcleanr.rules.prompts import CATEGORY_PROMPT

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


class LocalOllamaAdapter(AbstractAdapter):
    def __init__(
        self,
        model: str = "llama3",
        host: str = "http://localhost:11434",
        api_key: str | None = None,
    ):
        self.model = model
        self.host = host.rstrip("/")
        self.api_key = api_key
        (
            self.user_heuristics_text,
            self.global_heuristics_text,
        ) = load_heuristics_texts()

    def classify_transactions(self, transactions: Iterable) -> List[Dict[str, str | None]]:
        tx_objs = [normalise(tx) for tx in transactions]
        details: List[Dict[str, str | None]] = []
        for tx in tx_objs:
            prompt = CATEGORY_PROMPT.render(
                txn=tx,
                user_heuristics=self.user_heuristics_text,
                global_heuristics=self.global_heuristics_text,
            )
            try:
                resp = requests.post(
                    f"{self.host}/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": False},
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()
                details.append(
                    {"category": data.get("response", "").strip().lower(), "new_rule": None}
                )
            except Exception:
                details.append({"category": "unknown", "new_rule": None})
        self.last_details = details
        return details
