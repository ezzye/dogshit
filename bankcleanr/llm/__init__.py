from __future__ import annotations

from typing import Iterable, List, Dict, Type

from bankcleanr.settings import get_settings
from bankcleanr.transaction import normalise, Transaction
from bankcleanr.rules import heuristics

from .base import AbstractAdapter
from .openai import OpenAIAdapter
from .anthropic import AnthropicAdapter
from .mistral import MistralAdapter
from .local_ollama import LocalOllamaAdapter

# Mapping of provider names to adapter classes
PROVIDERS: Dict[str, Type[AbstractAdapter]] = {
    "openai": OpenAIAdapter,
    "anthropic": AnthropicAdapter,
    "mistral": MistralAdapter,
    "ollama": LocalOllamaAdapter,
}


def get_adapter(provider: str | None = None) -> AbstractAdapter:
    """Instantiate the adapter for the configured provider."""
    settings = get_settings()
    provider = provider or settings.llm_provider
    adapter_cls = PROVIDERS.get(provider, OpenAIAdapter)
    return adapter_cls(api_key=settings.api_key)


def classify_transactions(transactions: Iterable, provider: str | None = None) -> List[str]:
    """Classify transactions using heuristics and an optional LLM provider."""
    tx_objs = [normalise(tx) for tx in transactions]
    labels = heuristics.classify_transactions(tx_objs)

    unmatched: List[Transaction] = []
    unmatched_indexes: List[int] = []
    for idx, (tx, label) in enumerate(zip(tx_objs, labels)):
        if label == "unknown":
            unmatched.append(tx)
            unmatched_indexes.append(idx)

    if unmatched:
        adapter = get_adapter(provider)
        llm_labels = adapter.classify_transactions(unmatched)
        for idx, llm_label in zip(unmatched_indexes, llm_labels):
            labels[idx] = llm_label

    return labels
