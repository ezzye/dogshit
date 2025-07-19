from __future__ import annotations

from typing import Iterable, List, Dict, Type, Callable
import logging

from bankcleanr.settings import get_settings
from bankcleanr.transaction import normalise, Transaction, mask_transaction
from bankcleanr.rules import heuristics

from .base import AbstractAdapter
from .openai import OpenAIAdapter
from .anthropic import AnthropicAdapter
from .mistral import MistralAdapter
from .local_ollama import LocalOllamaAdapter
from .gemini import GeminiAdapter
from .bfl import BFLAdapter

logger = logging.getLogger(__name__)

# Mapping of provider names to adapter classes
PROVIDERS: Dict[str, Type[AbstractAdapter]] = {
    "openai": OpenAIAdapter,
    "anthropic": AnthropicAdapter,
    "mistral": MistralAdapter,
    "ollama": LocalOllamaAdapter,
    "gemini": GeminiAdapter,
    "bfl": BFLAdapter,
}


def get_adapter(provider: str | None = None) -> AbstractAdapter:
    """Instantiate the adapter for the configured provider."""
    settings = get_settings()
    provider = provider or settings.llm_provider
    adapter_cls = PROVIDERS.get(provider, OpenAIAdapter)
    return adapter_cls(api_key=settings.api_key)


def classify_transactions(
    transactions: Iterable,
    provider: str | None = None,
    confirm: Callable[[str], str] | None = None,
) -> List[str]:
    """Classify transactions using heuristics and an optional LLM provider."""
    tx_objs = [normalise(tx) for tx in transactions]
    labels = heuristics.classify_transactions(tx_objs)
    logger.debug("[classify_transactions] heuristic labels: %s", labels)

    unmatched: List[Transaction] = []
    unmatched_indexes: List[int] = []
    for idx, (tx, label) in enumerate(zip(tx_objs, labels)):
        if label == "unknown":
            unmatched.append(tx)
            unmatched_indexes.append(idx)

    if unmatched:
        logger.debug(
            "[classify_transactions] %d unmatched -> provider %s",
            len(unmatched),
            provider or get_settings().llm_provider,
        )
        adapter = get_adapter(provider)
        masked = [mask_transaction(tx) for tx in unmatched]
        logger.debug(
            "[classify_transactions] masked: %s",
            [tx.description for tx in masked],
        )
        llm_labels = adapter.classify_transactions(masked)
        logger.debug("[classify_transactions] llm labels: %s", llm_labels)
        for idx, llm_label in zip(unmatched_indexes, llm_labels):
            labels[idx] = llm_label

    heuristics.learn_new_patterns(tx_objs, labels, confirm=confirm)

    refreshed = heuristics.classify_transactions(tx_objs)
    for idx in unmatched_indexes:
        if refreshed[idx] != "unknown":
            labels[idx] = refreshed[idx]

    return labels
