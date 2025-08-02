"""Adapter for the fictional BFL API.

This implementation simply proxies to OpenAI for testing purposes."""

from __future__ import annotations

from typing import Dict, Iterable, List

from .openai import OpenAIAdapter
from .base import AbstractAdapter
from .retry import retry


class BFLAdapter(AbstractAdapter):
    def __init__(self, *args, **kwargs):
        self.delegate = OpenAIAdapter(*args, **kwargs)

    @retry()
    def _delegate_classify(self, transactions: Iterable) -> List[Dict[str, str | None]]:
        return self.delegate.classify_transactions(transactions)

    def classify_transactions(self, transactions: Iterable) -> List[Dict[str, str | None]]:
        try:
            details = self._delegate_classify(transactions)
        except Exception:
            details = [{"category": "unknown", "new_rule": None} for _ in transactions]
        for d in details:
            d.setdefault("new_rule", None)
        self.last_details = details
        return details
