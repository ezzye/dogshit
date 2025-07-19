"""Adapter for the Mistral AI chat models."""

from __future__ import annotations

from typing import Iterable, List
from pathlib import Path

from .base import AbstractAdapter
from bankcleanr.transaction import normalise
from bankcleanr.rules.prompts import CATEGORY_PROMPT

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


class MistralAdapter(AbstractAdapter):
    def __init__(
        self,
        model: str = "mistral-small",
        api_key: str | None = None,
        heuristics_path: Path = DATA_DIR / "heuristics.yml",
        cancellation_path: Path = DATA_DIR / "cancellation.yml",
    ):
        try:
            from mistralai.client import MistralClient
        except Exception:  # pragma: no cover - library may not be installed
            self.client = None
        else:
            self.client = MistralClient(api_key=api_key)
        self.model = model
        self.heuristics_text = (
            heuristics_path.read_text() if heuristics_path.exists() else ""
        )
        self.cancellation_text = (
            cancellation_path.read_text() if cancellation_path.exists() else ""
        )

    def classify_transactions(self, transactions: Iterable) -> List[str]:
        tx_objs = [normalise(tx) for tx in transactions]
        if self.client is None:
            return ["unknown" for _ in tx_objs]

        labels: List[str] = []
        for tx in tx_objs:
            prompt = CATEGORY_PROMPT.render(
                description=tx.description,
                heuristics=self.heuristics_text,
                cancellation=self.cancellation_text,
            )
            resp = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
            )
            message = resp.choices[0].message.content if resp.choices else ""
            labels.append(message.strip().lower())
        return labels
