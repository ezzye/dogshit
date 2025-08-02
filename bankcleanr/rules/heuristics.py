"""Local heuristics for quick transaction classification."""

from typing import Iterable, List

from bankcleanr.transaction import normalise
from . import regex


def classify_transactions(transactions: Iterable) -> List[str]:
    """Classify transactions locally using regex patterns."""
    labels: List[str] = []
    for tx in transactions:
        tx_obj = normalise(tx)
        labels.append(regex.classify(tx_obj.description))
    return labels
