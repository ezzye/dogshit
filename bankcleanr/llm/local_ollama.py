"""Adapter for a locally running Ollama server."""

from __future__ import annotations

from typing import Iterable, List
import requests

from .base import AbstractAdapter
from bankcleanr.transaction import normalise
from bankcleanr.rules.prompts import CATEGORY_PROMPT


class LocalOllamaAdapter(AbstractAdapter):
    def __init__(self, model: str = "llama3", host: str = "http://localhost:11434", api_key: str | None = None):
        self.model = model
        self.host = host.rstrip("/")
        self.api_key = api_key

    def classify_transactions(self, transactions: Iterable) -> List[str]:
        tx_objs = [normalise(tx) for tx in transactions]
        labels: List[str] = []
        for tx in tx_objs:
            prompt = CATEGORY_PROMPT.render(description=tx.description)
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
