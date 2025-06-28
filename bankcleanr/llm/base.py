from abc import ABC, abstractmethod
from typing import List, Mapping


class AbstractAdapter(ABC):
    """Base interface for LLM adapters."""

    @abstractmethod
    def classify_transactions(self, transactions: List[Mapping]) -> List[str]:
        """Return a label for each transaction."""
        raise NotImplementedError
