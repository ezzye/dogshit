from __future__ import annotations

import asyncio
import json
from typing import Iterable, List, Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from tenacity import retry, wait_random_exponential, stop_after_attempt

from .base import AbstractAdapter
from bankcleanr.transaction import normalise, Transaction
from bankcleanr.rules.prompts import CATEGORY_PROMPT


class OpenAIAdapter(AbstractAdapter):
    """Adapter for OpenAI's chat models using LangChain."""

    def __init__(self, model: str = "gpt-3.5-turbo", api_key: str | None = None):
        self.llm = ChatOpenAI(model=model, api_key=api_key)

    @retry(wait=wait_random_exponential(min=1, max=2), stop=stop_after_attempt(3))
    async def _aclassify(self, tx: Transaction) -> Dict[str, Any]:
        prompt = CATEGORY_PROMPT.render(description=tx.description)
        message = HumanMessage(content=prompt)
        result = await self.llm.apredict_messages([message])
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
        results = asyncio.run(self._aclassify_batch(tx_objs))
        self.last_details = results
        return [res.get("category", "unknown") for res in results]
