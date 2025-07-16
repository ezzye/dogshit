"""Local heuristics for quick transaction classification."""

from typing import Iterable, List, Callable, Optional
import sys

from bankcleanr.transaction import Transaction, normalise
from . import regex


def classify_transactions(transactions: Iterable) -> List[str]:
    """Classify transactions locally using regex patterns."""
    labels: List[str] = []
    for tx in transactions:
        tx_obj = normalise(tx)
        labels.append(regex.classify(tx_obj.description))
    return labels


def learn_new_patterns(
    transactions: Iterable[Transaction],
    labels: Iterable[str],
    confirm: Optional[Callable[[str], str]] = None,
) -> None:
    """Ask to store new regex patterns derived from LLM labels."""
    if confirm is None:
        def confirm(prompt: str) -> str:
            if not sys.stdin.isatty():
                return "n"
            try:
                return input(prompt)
            except (EOFError, OSError):
                return "n"

    for tx, label in zip(transactions, labels):
        if label == "unknown":
            continue
        current = regex.classify(tx.description)
        if current == "unknown":
            prompt = f"Add pattern for '{label}' matching '{tx.description}'? [y/N] "
            answer = confirm(prompt)
            if answer and answer.lower().startswith("y"):
                regex.add_pattern(label, tx.description)
                regex.reload_patterns()


