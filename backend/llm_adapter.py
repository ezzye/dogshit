"""LLM adapter with cost tracking and retry logic."""

from __future__ import annotations

import json
import logging
import os
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from contextlib import contextmanager
from datetime import date
from typing import Callable, Dict, Iterable, List, Tuple

from .database import get_session
from .models import LLMCost


logger = logging.getLogger(__name__)


class DailyCostTracker:
    """Track per-job and per-day LLM costs."""

    def __init__(self, limit: float, job_limit: float = float(os.getenv("MAX_JOB_COST_GBP", "5.0"))) -> None:
        self.limit = limit
        self.job_limit = job_limit
        self.reset()

    def reset(self) -> None:
        self.day = date.today()
        self.daily_total = 0.0
        self.job_costs: Dict[int, float] = defaultdict(float)

    def add(self, job_id: int, tokens_in: int, tokens_out: int, cost_gbp: float) -> None:
        today = date.today()
        if today != self.day:
            self.reset()
        if self.daily_total + cost_gbp > self.limit:
            raise RuntimeError("Daily cost limit exceeded")
        if self.job_costs[job_id] + cost_gbp > self.job_limit:
            raise RuntimeError("Job cost limit exceeded")
        self.daily_total += cost_gbp
        self.job_costs[job_id] += cost_gbp
        for session in get_session():
            session.add(
                LLMCost(
                    job_id=job_id,
                    tokens_in=tokens_in,
                    tokens_out=tokens_out,
                    estimated_cost_gbp=cost_gbp,
                )
            )
            session.commit()
        logger.info(
            "job %s cost %.4f GBP (job total %.4f, daily total %.4f)",
            job_id,
            cost_gbp,
            self.job_costs[job_id],
            self.daily_total,
        )

    def add_raw_cost(self, job_id: int, cost_gbp: float) -> None:
        """Record a non-token-based cost."""
        self.add(job_id, 0, 0, cost_gbp)

    @contextmanager
    def track(
        self,
        job_id: int,
        cost: float,
        tokens_in: int = 0,
        tokens_out: int = 0,
    ):
        """Context manager to record cost after a block completes."""
        try:
            yield
        finally:
            self.add(job_id, tokens_in, tokens_out, cost)


_DAILY_LIMIT = float(os.getenv("MAX_DAILY_COST_GBP", "1.0"))
_JOB_LIMIT = float(os.getenv("MAX_JOB_COST_GBP", "5.0"))
cost_tracker = DailyCostTracker(_DAILY_LIMIT, _JOB_LIMIT)


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
            tokens_in = usage.get("prompt_tokens", usage.get("total_tokens", 0))
            tokens_out = usage.get("completion_tokens", 0)
            tokens = tokens_in + tokens_out
            cost_gbp = tokens / 1000 * self.price_per_1k_tokens_gbp
            cost_tracker.add(job_id, tokens_in, tokens_out, cost_gbp)
            for label, confidence in data.get("labels", []):
                responses.append(
                    {
                        "label": label,
                        "confidence": confidence,
                        "tokens": tokens,
                        "cost": cost_gbp,
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
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            'Respond ONLY with JSON of the form '
                            '{"label": "<label>", "confidence": <number>}.'
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )
            content = resp.choices[0].message.content or ""
            try:
                data = json.loads(content)
                label = data.get("label", "").strip()
                confidence = float(data.get("confidence", 0.0))
            except json.JSONDecodeError:
                logger.warning("Non-JSON response from model: %s", content)
                label = content.strip()
                confidence = 0.0
            except (TypeError, KeyError, ValueError) as exc:
                logger.error("Malformed JSON response from model: %s", content)
                raise ValueError("Malformed model response") from exc
            labels.append((label, confidence))
            total_tokens += getattr(resp.usage, "total_tokens", 0)
        return {"labels": labels, "usage": {"total_tokens": total_tokens}}


class AnthropicAdapter(AbstractAdapter):
    """Adapter for Anthropic models."""

    def __init__(self, model: str = "claude-3-haiku", **kwargs):
        super().__init__(model, **kwargs)

    def _send(self, prompts: List[str]) -> Dict:  # pragma: no cover - external API
        raise NotImplementedError("Anthropic adapter requires external API access")


class AzureAdapter(AbstractAdapter):
    """Adapter for Azure-hosted models."""

    def __init__(self, model: str = "gpt-4o-mini", **kwargs):
        super().__init__(model, **kwargs)

    def _send(self, prompts: List[str]) -> Dict:  # pragma: no cover - external API
        raise NotImplementedError("Azure adapter requires external API access")


_providers: Dict[str, Callable[[], AbstractAdapter]] = {}
_adapter_instances: Dict[str, AbstractAdapter] = {}


def register_provider(name: str, factory: Callable[[], AbstractAdapter]) -> None:
    _providers[name.lower()] = factory


def get_provider_name() -> str:
    provider = os.getenv("LLM_PROVIDER")
    if provider:
        return provider.lower()
    config_file = os.getenv("LLM_CONFIG_FILE")
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file) as fh:
                data = json.load(fh)
            cfg_provider = data.get("llm_provider")
            if cfg_provider:
                return cfg_provider.lower()
        except Exception:  # pragma: no cover - invalid config
            pass
    return "openai"


def get_adapter(provider_name: str | None = None) -> AbstractAdapter:
    name = (provider_name or get_provider_name()).lower()
    adapter = _adapter_instances.get(name)
    if adapter is None:
        factory = _providers.get(name)
        if factory is None:
            raise ValueError(f"Unknown LLM provider {name}")
        adapter = factory()
        _adapter_instances[name] = adapter
    return adapter


register_provider("openai", OpenAIAdapter)
register_provider("anthropic", AnthropicAdapter)
register_provider("azure", AzureAdapter)


__all__ = [
    "AbstractAdapter",
    "OpenAIAdapter",
    "AnthropicAdapter",
    "AzureAdapter",
    "get_adapter",
    "register_provider",
    "cost_tracker",
    "DailyCostTracker",
]

