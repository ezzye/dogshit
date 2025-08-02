"""Adapter for Anthropic's Claude API."""

from __future__ import annotations

from typing import Dict, Iterable, List
from pathlib import Path
import json
import re
import logging

from .base import AbstractAdapter
from .utils import load_heuristics_texts
from .retry import retry
from .cost_manager import cost_manager, estimate_tokens
from bankcleanr.transaction import normalise
from bankcleanr.rules.prompts import CATEGORY_PROMPT

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

logger = logging.getLogger(__name__)


class AnthropicAdapter(AbstractAdapter):
    def __init__(
        self,
        model: str = "claude-3-haiku-20240307",
        api_key: str | None = None,
        price_per_token: float = 0.000002,
    ):
        try:
            import anthropic
        except Exception:  # pragma: no cover - library may not be installed
            self.client = None
        else:
            self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.price_per_token = price_per_token
        (self.user_heuristics_text, self.global_heuristics_text) = load_heuristics_texts()

    @retry()
    def _create_message(self, prompt: str):
        return self.client.messages.create(
            model=self.model,
            max_tokens=5,
            messages=[{"role": "user", "content": prompt}],
        )

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
            try:
                tokens = estimate_tokens(prompt)
                cost_manager.check_and_add(tokens * self.price_per_token)
                resp = self._create_message(prompt)
            except RuntimeError:
                raise
            except Exception as exc:
                logger.debug("[AnthropicAdapter] error: %s", exc)
                details.append({"category": "unknown", "new_rule": None})
                continue
            content = resp.content[0].text if hasattr(resp.content[0], "text") else resp.content
            content = content.strip()
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
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug("[AnthropicAdapter] parse error: %s", exc)
                details.append({"category": content.lower(), "new_rule": None})
        self.last_details = details
        return details
