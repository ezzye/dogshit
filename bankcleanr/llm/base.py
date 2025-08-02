from abc import ABC, abstractmethod
from typing import Dict, List, Mapping, Optional


class AbstractAdapter(ABC):
    """Base interface for LLM adapters."""

    last_details: List[Dict[str, Optional[str]]]

    @abstractmethod
    def classify_transactions(
        self, transactions: List[Mapping]
    ) -> List[Dict[str, Optional[str]]]:
        """Return classification details for each transaction.

        Each result is a dictionary containing at least the key ``category`` and
        optionally ``new_rule`` which, when provided, represents a heuristic
        regex pattern suggested by the LLM.
        """
        raise NotImplementedError
