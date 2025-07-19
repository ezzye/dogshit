from __future__ import annotations

import asyncio
import json
import re
import logging
from typing import Iterable, List, Dict, Any
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from tenacity import retry, wait_random_exponential, stop_after_attempt

from .base import AbstractAdapter
from bankcleanr.transaction import normalise, Transaction
from bankcleanr.rules.prompts import CATEGORY_PROMPT

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


logger = logging.getLogger(__name__)


class OpenAIAdapter(AbstractAdapter):
    """Adapter for OpenAI's chat models using LangChain."""

    def __init__(
        self,
        model: str = "gpt-3.5-turbo",
        api_key: str | None = None,
        max_concurrency: int = 5,
        heuristics_path: Path = DATA_DIR / "heuristics.yml",
        cancellation_path: Path = DATA_DIR / "cancellation.yml",
    ):
        self.llm = ChatOpenAI(model=model, api_key=api_key)
        # Limit the number of concurrent API calls
        self._sem = asyncio.Semaphore(max_concurrency)
        self.heuristics_text = (
            heuristics_path.read_text() if heuristics_path.exists() else ""
        )
        self.cancellation_text = (
            cancellation_path.read_text() if cancellation_path.exists() else ""
        )

    @retry(wait=wait_random_exponential(min=1, max=2), stop=stop_after_attempt(3))
    async def _aclassify(self, tx: Transaction) -> Dict[str, Any]:
        async with self._sem:
            prompt = CATEGORY_PROMPT.render(
                description=tx.description,
                heuristics=self.heuristics_text,
                cancellation=self.cancellation_text,
            )
            logger.debug("Rendered prompt: %s", prompt)
            message = HumanMessage(content=prompt)
            result = await self.llm.ainvoke([message])
        logger.debug("LLM response: %s", result.content)
        try:
            content = result.content.strip()
            if content.startswith("```") and content.endswith("```"):
                content = content[3:-3].strip()
                content = re.sub(r"^json\s*", "", content, flags=re.IGNORECASE)
            data = json.loads(content)
            if not isinstance(data, dict):
                raise ValueError
        except Exception:
            data = {
                "category": result.content.strip().lower(),
                "reasons_to_cancel": [],
                "checklist": [],
            }
        return data

    async def _aclassify_batch(self, txs: Iterable[Transaction]) -> List[Dict[str, Any]]:
        tasks = [self._aclassify(tx) for tx in txs]
        return await asyncio.gather(*tasks)

    def classify_transactions(self, transactions: Iterable) -> List[str]:
        tx_objs = [normalise(tx) for tx in transactions]
        try:
            results = asyncio.run(self._aclassify_batch(tx_objs))
        except Exception as exc:
            logger.error("Failed to classify transactions: %s", exc)
            self.last_details = [
                {"category": "unknown", "reasons_to_cancel": [], "checklist": []}
                for _ in tx_objs
            ]
            return ["unknown" for _ in tx_objs]

        self.last_details = results
        return [res.get("category", "unknown") for res in results]
