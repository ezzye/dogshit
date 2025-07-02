"""Adapter for Anthropic's Claude API."""

from __future__ import annotations

from typing import Iterable, List

from .base import AbstractAdapter
from bankcleanr.transaction import normalise, Transaction
from bankcleanr.rules.prompts import CATEGORY_PROMPT


class AnthropicAdapter(AbstractAdapter):
    def __init__(self, model: str = "claude-3-haiku-20240307", api_key: str | None = None):
        try:
            import anthropic
        except Exception:  # pragma: no cover - library may not be installed
            self.client = None
        else:
            self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def classify_transactions(self, transactions: Iterable) -> List[str]:
        tx_objs = [normalise(tx) for tx in transactions]
        if self.client is None:
            return ["unknown" for _ in tx_objs]

        labels: List[str] = []
        for tx in tx_objs:
            prompt = CATEGORY_PROMPT.render(description=tx.description)
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=5,
                messages=[{"role": "user", "content": prompt}],
            )
            content = resp.content[0].text if hasattr(resp.content[0], "text") else resp.content
            labels.append(content.strip().lower())
        return labels
