"""Adapter for Anthropic's Claude API."""

from __future__ import annotations

from typing import Dict, Iterable, List
from pathlib import Path

from .base import AbstractAdapter
from .utils import load_heuristics_texts
from bankcleanr.transaction import normalise
from bankcleanr.rules.prompts import CATEGORY_PROMPT

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


class AnthropicAdapter(AbstractAdapter):
    def __init__(
        self,
        model: str = "claude-3-haiku-20240307",
        api_key: str | None = None,
    ):
        try:
            import anthropic
        except Exception:  # pragma: no cover - library may not be installed
            self.client = None
        else:
            self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        (self.user_heuristics_text, self.global_heuristics_text) = load_heuristics_texts()

    def classify_transactions(self, transactions: Iterable) -> List[Dict[str, str | None]]:
        tx_objs = [normalise(tx) for tx in transactions]
        if self.client is None:
            details = [
                {"category": "unknown", "new_rule": None} for _ in tx_objs
            ]
            self.last_details = details
            return details

        details: List[Dict[str, str | None]] = []
        for tx in tx_objs:
            prompt = CATEGORY_PROMPT.render(
                txn=tx,
                user_heuristics=self.user_heuristics_text,
                global_heuristics=self.global_heuristics_text,
            )
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=5,
                messages=[{"role": "user", "content": prompt}],
            )
            content = resp.content[0].text if hasattr(resp.content[0], "text") else resp.content
            details.append({"category": content.strip().lower(), "new_rule": None})
        self.last_details = details
        return details
