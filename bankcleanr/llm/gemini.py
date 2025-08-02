"""Adapter for Google's Gemini API."""

from __future__ import annotations

from typing import Dict, Iterable, List
from pathlib import Path
import logging
import json
import re

from .base import AbstractAdapter
from .utils import load_heuristics_texts
from .retry import retry
from bankcleanr.transaction import normalise
from bankcleanr.rules.prompts import CATEGORY_PROMPT

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


logger = logging.getLogger(__name__)


class GeminiAdapter(AbstractAdapter):
    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        api_key: str | None = None,
    ):
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
        (
            self.user_heuristics_text,
            self.global_heuristics_text,
        ) = load_heuristics_texts()

    @retry()
    def _generate_content(self, prompt: str):
        return self.client.models.generate_content(model=self.model, contents=prompt)

    def classify_transactions(self, transactions: Iterable) -> List[Dict[str, str | None]]:
        tx_objs = [normalise(tx) for tx in transactions]
        if self.client is None:
            logger.debug("[GeminiAdapter] no client available")
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
            logger.debug("[GeminiAdapter] prompt: %s", prompt)
            try:
                resp = self._generate_content(prompt)
            except Exception as exc:
                logger.debug("[GeminiAdapter] error: %s", exc)
                details.append({"category": "unknown", "new_rule": None})
                continue
            logger.debug("[GeminiAdapter] raw response: %s", resp)
            message = resp.text if hasattr(resp, "text") else resp.candidates[0].content
            logger.debug("[GeminiAdapter] message: %s", message)
            content = message.strip()
            try:
                if content.startswith("```") and content.endswith("```"):
                    content = content[3:-3].strip()
                    content = re.sub(r"^json\s*", "", content, flags=re.IGNORECASE)
                data = json.loads(content)
                if not isinstance(data, dict):
                    raise ValueError
                details.append(
                    {
                        "category": str(data.get("category", "unknown")),
                        "new_rule": data.get("new_rule"),
                    }
                )
            except Exception as exc:
                logger.debug("[GeminiAdapter] parse error: %s", exc)
                details.append({"category": content.lower(), "new_rule": None})
        self.last_details = details
        return details
