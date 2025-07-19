"""Local heuristics for quick transaction classification."""

from typing import Iterable, List, Callable, Optional, Tuple
import sys
from collections import OrderedDict

from bankcleanr.transaction import Transaction, normalise
from . import regex


def classify_transactions(transactions: Iterable) -> List[str]:
    """Classify transactions locally using regex patterns."""
    labels: List[str] = []
    for tx in transactions:
        tx_obj = normalise(tx)
        labels.append(regex.classify(tx_obj.description))
    return labels


def group_unmatched_transactions(
    transactions: Iterable[Transaction],
    labels: Iterable[str],
) -> List[Tuple[str, str, int]]:
    """Return unmatched transactions grouped by description with counts."""
    counts: OrderedDict[Tuple[str, str], int] = OrderedDict()
    for tx, label in zip(transactions, labels):
        if label == "unknown":
            continue
        if regex.classify(tx.description) == "unknown":
            key = (label, tx.description)
            counts[key] = counts.get(key, 0) + 1
    return [(label, desc, count) for (label, desc), count in counts.items()]


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

    groups = group_unmatched_transactions(transactions, labels)
    if groups:
        print("Unmatched transaction summary:")
        for label, description, count in groups:
            suffix = f" ({count})" if count > 1 else ""
            print(f"- {description}{suffix} -> {label}")

    for label, description, _ in groups:
        prompt = f"Add pattern for '{label}' matching '{description}'? [y/N] "
        answer = confirm(prompt)
        if answer and answer.lower().startswith("y"):
            regex.add_pattern(label, description)
            regex.reload_patterns()


