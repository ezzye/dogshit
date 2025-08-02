"""Adapter for a locally running Ollama server."""

from __future__ import annotations

from typing import Dict, Iterable, List
from pathlib import Path
import requests
import json
import re
import logging

from .base import AbstractAdapter
from .utils import load_heuristics_texts
from .retry import retry
from bankcleanr.transaction import normalise
from bankcleanr.rules.prompts import CATEGORY_PROMPT

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

logger = logging.getLogger(__name__)


class LocalOllamaAdapter(AbstractAdapter):
    def __init__(
        self,
        model: str = "llama3",
        host: str = "http://localhost:11434",
        api_key: str | None = None,
    ):
        self.model = model
        self.host = host.rstrip("/")
        self.api_key = api_key
        (
            self.user_heuristics_text,
            self.global_heuristics_text,
        ) = load_heuristics_texts()

    @retry()
    def _generate(self, prompt: str):
        resp = requests.post(
            f"{self.host}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def classify_transactions(self, transactions: Iterable) -> List[Dict[str, str | None]]:
        tx_objs = [normalise(tx) for tx in transactions]
        details: List[Dict[str, str | None]] = []
        for tx in tx_objs:
            prompt = CATEGORY_PROMPT.render(
                txn=tx,
                user_heuristics=self.user_heuristics_text,
                global_heuristics=self.global_heuristics_text,
            )
            try:
                data = self._generate(prompt)
                message = data.get("response", "")
                content = message.strip()
                try:
                    if content.startswith("```") and content.endswith("```"):
                        content = content[3:-3].strip()
                        content = re.sub(r"^json\s*", "", content, flags=re.IGNORECASE)
                    parsed = json.loads(content)
                    if not isinstance(parsed, dict):
                        raise ValueError
                    details.append(
                        {
                            "category": str(parsed.get("category", "unknown")),
                            "new_rule": parsed.get("new_rule"),
                        }
                    )
                except Exception as exc:
                    logger.debug("[LocalOllamaAdapter] parse error: %s", exc)
                    details.append({"category": content.lower(), "new_rule": None})
            except Exception as exc:
                logger.debug("[LocalOllamaAdapter] error: %s", exc)
                details.append({"category": "unknown", "new_rule": None})
        self.last_details = details
        return details
