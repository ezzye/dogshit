from abc import ABC, abstractmethod
from typing import List, Mapping, Optional, TypedDict


class ClassificationDetail(TypedDict, total=False):
    """Structured result for a classified transaction."""

    category: str
    new_rule: Optional[str]


class AbstractAdapter(ABC):
    """Base interface for LLM adapters."""

    last_details: List[ClassificationDetail]

    @abstractmethod
    def classify_transactions(
        self, transactions: List[Mapping]
    ) -> List[ClassificationDetail]:
        """Return classification details for each transaction.

        Each result is a dictionary containing at least the key ``category`` and
        optionally ``new_rule`` which, when provided, represents a heuristic
        regex pattern suggested by the LLM.
        """
        raise NotImplementedError
