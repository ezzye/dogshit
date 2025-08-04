"""LLM adapter with cost tracking and retry logic."""

from __future__ import annotations

import logging
import os
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import date
from typing import Dict, Iterable, List, Tuple


logger = logging.getLogger(__name__)


class DailyCostTracker:
    """Track per-job and per-day LLM costs."""

    def __init__(self, limit: float) -> None:
        self.limit = limit
        self.reset()

    def reset(self) -> None:
        self.day = date.today()
        self.daily_total = 0.0
        self.job_costs: Dict[int, float] = defaultdict(float)

    def add(self, job_id: int, cost: float) -> None:
        today = date.today()
        if today != self.day:
            self.reset()
        if self.daily_total + cost > self.limit:
            raise RuntimeError("Daily cost limit exceeded")
        self.daily_total += cost
        self.job_costs[job_id] += cost
        logger.info(
            "job %s cost %.4f GBP (daily total %.4f)",
            job_id,
            cost,
            self.daily_total,
        )


_DAILY_LIMIT = float(os.getenv("MAX_DAILY_COST_GBP", "1.0"))
cost_tracker = DailyCostTracker(_DAILY_LIMIT)


def _chunks(items: Iterable[str], size: int) -> Iterable[List[str]]:
    items = list(items)
    for i in range(0, len(items), size):
        yield items[i : i + size]


class AbstractAdapter(ABC):
    """Base adapter providing batching, retries and cost tracking."""

    price_per_1k_tokens_gbp: float = float(
        os.getenv("PRICE_PER_1K_TOKENS_GBP", "0.002")
    )

    def __init__(self, model: str, batch_size: int = 20, max_retries: int = 3):
        self.model = model
        self.batch_size = batch_size
        self.max_retries = max_retries

    @abstractmethod
    def _send(self, prompts: List[str]) -> Dict:
        """Send a batch of prompts to the underlying model."""

    def classify(self, prompts: List[str], job_id: int) -> List[Dict[str, float]]:
        responses: List[Dict[str, float]] = []
        for batch in _chunks(prompts, self.batch_size):
            def call() -> Dict:
                return self._send(batch)

            for attempt in range(self.max_retries):
                try:
                    data = call()
                    break
                except Exception:  # pragma: no cover - transient
                    if attempt == self.max_retries - 1:
                        raise
                    time.sleep(2 ** attempt)
            usage = data.get("usage", {})
            tokens = usage.get("total_tokens", 0)
            cost = tokens / 1000 * self.price_per_1k_tokens_gbp
            cost_tracker.add(job_id, cost)
            for label, confidence in data.get("labels", []):
                responses.append(
                    {
                        "label": label,
                        "confidence": confidence,
                        "tokens": tokens,
                        "cost": cost,
                    }
                )
        return responses


class OpenAIAdapter(AbstractAdapter):
    """Adapter using the OpenAI client."""

    def __init__(self, model: str = "gpt-4o-mini", **kwargs):
        import openai

        super().__init__(model, **kwargs)
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = openai.OpenAI(api_key=api_key)

    def _send(self, prompts: List[str]) -> Dict:
        labels: List[Tuple[str, float]] = []
        total_tokens = 0
        for prompt in prompts:
            resp = self.client.chat.completions.create(
                model=self.model, messages=[{"role": "user", "content": prompt}]
            )
            labels.append((resp.choices[0].message.content.strip(), 1.0))
            total_tokens += getattr(resp.usage, "total_tokens", 0)
        return {"labels": labels, "usage": {"total_tokens": total_tokens}}


_adapter_instance: AbstractAdapter | None = None


def get_adapter() -> AbstractAdapter:
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = OpenAIAdapter()
    return _adapter_instance


__all__ = [
    "AbstractAdapter",
    "OpenAIAdapter",
    "get_adapter",
    "cost_tracker",
    "DailyCostTracker",
]

