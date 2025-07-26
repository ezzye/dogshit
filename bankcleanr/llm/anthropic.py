"""Adapter for Anthropic's Claude API."""

from __future__ import annotations

from typing import Iterable, List
from pathlib import Path

from .base import AbstractAdapter
from bankcleanr.transaction import normalise
from bankcleanr.rules.prompts import CATEGORY_PROMPT

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


class AnthropicAdapter(AbstractAdapter):
    def __init__(
        self,
        model: str = "claude-3-haiku-20240307",
        api_key: str | None = None,
        heuristics_path: Path = DATA_DIR / "heuristics.yml",
        cancellation_path: Path = DATA_DIR / "cancellation.yml",
    ):
        try:
            import anthropic
        except Exception:  # pragma: no cover - library may not be installed
            self.client = None
        else:
            self.client = anthropic.Anthropic(api_key=api_key)
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
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=5,
                messages=[{"role": "user", "content": prompt}],
            )
            content = resp.content[0].text if hasattr(resp.content[0], "text") else resp.content
            labels.append(content.strip().lower())
        return labels
