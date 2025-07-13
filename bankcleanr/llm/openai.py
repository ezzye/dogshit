from __future__ import annotations

import asyncio
import json
import logging
from typing import Iterable, List, Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from tenacity import retry, wait_random_exponential, stop_after_attempt

from .base import AbstractAdapter
from bankcleanr.transaction import normalise, Transaction
from bankcleanr.rules.prompts import CATEGORY_PROMPT


logger = logging.getLogger(__name__)


class OpenAIAdapter(AbstractAdapter):
    """Adapter for OpenAI's chat models using LangChain."""

    def __init__(
        self,
        model: str = "gpt-3.5-turbo",
        api_key: str | None = None,
        max_concurrency: int = 5,
    ):
        self.llm = ChatOpenAI(model=model, api_key=api_key)
        # Limit the number of concurrent API calls
        self._sem = asyncio.Semaphore(max_concurrency)

    @retry(wait=wait_random_exponential(min=1, max=2), stop=stop_after_attempt(3))
    async def _aclassify(self, tx: Transaction) -> Dict[str, Any]:
        async with self._sem:
            prompt = CATEGORY_PROMPT.render(description=tx.description)
            logger.debug("Rendered prompt: %s", prompt)
            message = HumanMessage(content=prompt)
            result = await self.llm.ainvoke([message])
        logger.debug("LLM response: %s", result.content)
        try:
            data = json.loads(result.content)
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
