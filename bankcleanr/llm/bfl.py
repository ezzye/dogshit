"""Adapter for the fictional BFL API.

This implementation simply proxies to OpenAI for testing purposes."""

from __future__ import annotations

from typing import Dict, Iterable, List

from .openai import OpenAIAdapter
from .base import AbstractAdapter


class BFLAdapter(AbstractAdapter):
    def __init__(self, *args, **kwargs):
        self.delegate = OpenAIAdapter(*args, **kwargs)

    def classify_transactions(self, transactions: Iterable) -> List[Dict[str, str | None]]:
        self.last_details = self.delegate.classify_transactions(transactions)
        return self.last_details
