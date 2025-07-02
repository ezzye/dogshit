"""Adapter for the Mistral AI chat models."""

from __future__ import annotations

from typing import Iterable, List

from .base import AbstractAdapter
from bankcleanr.transaction import normalise
from bankcleanr.rules.prompts import CATEGORY_PROMPT


class MistralAdapter(AbstractAdapter):
    def __init__(self, model: str = "mistral-small", api_key: str | None = None):
        try:
            from mistralai.client import MistralClient
        except Exception:  # pragma: no cover - library may not be installed
            self.client = None
        else:
            self.client = MistralClient(api_key=api_key)
        self.model = model

    def classify_transactions(self, transactions: Iterable) -> List[str]:
        tx_objs = [normalise(tx) for tx in transactions]
        if self.client is None:
            return ["unknown" for _ in tx_objs]

        labels: List[str] = []
        for tx in tx_objs:
            prompt = CATEGORY_PROMPT.render(description=tx.description)
            resp = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
            )
            message = resp.choices[0].message.content if resp.choices else ""
            labels.append(message.strip().lower())
        return labels
