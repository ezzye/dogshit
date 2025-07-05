"""Adapter for Google's Gemini API."""

from __future__ import annotations

from typing import Iterable, List

from .base import AbstractAdapter
from bankcleanr.transaction import normalise
from bankcleanr.rules.prompts import CATEGORY_PROMPT


class GeminiAdapter(AbstractAdapter):
    def __init__(self, model: str = "gemini-pro", api_key: str | None = None):
        try:
            import google.generativeai as genai  # type: ignore
        except Exception:  # pragma: no cover - library may not be installed
            self.client = None
        else:
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel(model)
        self.model = model

    def classify_transactions(self, transactions: Iterable) -> List[str]:
        tx_objs = [normalise(tx) for tx in transactions]
        if self.client is None:
            return ["unknown" for _ in tx_objs]

        labels: List[str] = []
        for tx in tx_objs:
            prompt = CATEGORY_PROMPT.render(description=tx.description)
            try:
                resp = self.client.generate_content(prompt, stream=False)
                message = resp.text if hasattr(resp, "text") else resp.candidates[0].content
                labels.append(message.strip().lower())
            except Exception:
                labels.append("unknown")
        return labels
