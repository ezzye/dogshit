"""Adapter for a locally running Ollama server."""

from __future__ import annotations

from typing import Iterable, List
from pathlib import Path
import requests

from .base import AbstractAdapter
from .utils import load_heuristics_text
from bankcleanr.transaction import normalise
from bankcleanr.rules.prompts import CATEGORY_PROMPT

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


class LocalOllamaAdapter(AbstractAdapter):
    def __init__(
        self,
        model: str = "llama3",
        host: str = "http://localhost:11434",
        api_key: str | None = None,
        cancellation_path: Path = DATA_DIR / "cancellation.yml",
    ):
        self.model = model
        self.host = host.rstrip("/")
        self.api_key = api_key
        self.heuristics_text = load_heuristics_text()
        self.cancellation_text = (
            cancellation_path.read_text() if cancellation_path.exists() else ""
        )

    def classify_transactions(self, transactions: Iterable) -> List[str]:
        tx_objs = [normalise(tx) for tx in transactions]
        labels: List[str] = []
        for tx in tx_objs:
            prompt = CATEGORY_PROMPT.render(
                description=tx.description,
                heuristics=self.heuristics_text,
                cancellation=self.cancellation_text,
            )
            try:
                resp = requests.post(
                    f"{self.host}/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": False},
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()
                labels.append(data.get("response", "").strip().lower())
            except Exception:
                labels.append("unknown")
        return labels
