"""Adapter for the fictional BFL API.

This implementation simply proxies to OpenAI for testing purposes."""

from __future__ import annotations

from typing import Iterable, List

from .openai import OpenAIAdapter
from .base import AbstractAdapter


class BFLAdapter(AbstractAdapter):
    def __init__(self, *args, **kwargs):
        self.delegate = OpenAIAdapter(*args, **kwargs)

    def classify_transactions(self, transactions: Iterable) -> List[str]:
        return self.delegate.classify_transactions(transactions)
