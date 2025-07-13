"""Adapter for Google's Gemini API."""

from __future__ import annotations

from typing import Iterable, List

from .base import AbstractAdapter
from bankcleanr.transaction import normalise
from bankcleanr.rules.prompts import CATEGORY_PROMPT


class GeminiAdapter(AbstractAdapter):
    def __init__(self, model: str = "gemini-pro", api_key: str | None = None):
        """Initialise the Gemini adapter and underlying client."""
        try:
            import google.generativeai as genai  # type: ignore
        except Exception as exc:  # pragma: no cover - library may not be installed
            print(f"[GeminiAdapter] failed to import SDK: {exc}")
            self.client = None
        else:
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel(model)
            print(f"[GeminiAdapter] initialised model={model}")
        self.model = model

    def classify_transactions(self, transactions: Iterable) -> List[str]:
        tx_objs = [normalise(tx) for tx in transactions]
        if self.client is None:
            print("[GeminiAdapter] no client available")
            return ["unknown" for _ in tx_objs]

        labels: List[str] = []
        for tx in tx_objs:
            prompt = CATEGORY_PROMPT.render(description=tx.description)
            print(f"[GeminiAdapter] prompt: {prompt}")
            try:
                resp = self.client.generate_content(prompt, stream=False)
                print(f"[GeminiAdapter] raw response: {resp}")
                message = resp.text if hasattr(resp, "text") else resp.candidates[0].content
                print(f"[GeminiAdapter] message: {message}")
                labels.append(message.strip().lower())
            except Exception as exc:
                print(f"[GeminiAdapter] error: {exc}")
                import traceback
                traceback.print_exc()
                labels.append("unknown")
        return labels
