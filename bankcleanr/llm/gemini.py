"""Adapter for Google's Gemini API."""

from __future__ import annotations

from typing import Iterable, List
import logging

from .base import AbstractAdapter
from bankcleanr.transaction import normalise
from bankcleanr.rules.prompts import CATEGORY_PROMPT


logger = logging.getLogger(__name__)


class GeminiAdapter(AbstractAdapter):
    def __init__(self, model: str = "gemini-2.5-flash", api_key: str | None = None):
        """Initialise the Gemini adapter and underlying client."""
        try:
            from google import genai  # type: ignore
        except Exception as exc:  # pragma: no cover - library may not be installed
            logger.debug("[GeminiAdapter] failed to import SDK: %s", exc)
            self.client = None
        else:
            genai.configure(api_key=api_key)
            self.client = genai.Client()
            logger.debug("[GeminiAdapter] initialised model=%s", model)
        self.model = model

    def classify_transactions(self, transactions: Iterable) -> List[str]:
        tx_objs = [normalise(tx) for tx in transactions]
        if self.client is None:
            logger.debug("[GeminiAdapter] no client available")
            return ["unknown" for _ in tx_objs]

        labels: List[str] = []
        for tx in tx_objs:
            prompt = CATEGORY_PROMPT.render(description=tx.description)
            logger.debug("[GeminiAdapter] prompt: %s", prompt)
            try:
                resp = self.client.models.generate_content(
                    model=self.model, contents=prompt
                )
                logger.debug("[GeminiAdapter] raw response: %s", resp)
                message = (
                    resp.text if hasattr(resp, "text") else resp.candidates[0].content
                )
                logger.debug("[GeminiAdapter] message: %s", message)
                labels.append(message.strip().lower())
            except Exception as exc:
                logger.debug("[GeminiAdapter] error: %s", exc)
                import traceback

                traceback.print_exc()
                labels.append("unknown")
        return labels
