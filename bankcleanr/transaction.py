from dataclasses import dataclass, asdict, is_dataclass
from typing import Mapping, Any
import re

@dataclass
class Transaction:
    date: str
    description: str
    amount: str
    balance: str = ""

    def to_dict(self) -> Mapping[str, Any]:
        """Return transaction as a dictionary."""
        return asdict(self)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> 'Transaction':
        """Create a Transaction from a mapping object."""
        return cls(
            date=data.get("date", ""),
            description=data.get("description", ""),
            amount=data.get("amount", ""),
            balance=data.get("balance", ""),
        )


# utility to normalise

def normalise(tx: Any) -> 'Transaction':
    """Convert a dataclass or mapping into a Transaction."""
    if is_dataclass(tx):
        return tx  # type: ignore[return-value]
    if isinstance(tx, Mapping):
        return Transaction.from_mapping(tx)
    raise TypeError("Unsupported transaction type")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MASK_RE = re.compile(r"\b(?:\d{2}-?\d{2}-?\d{2}|\d{6}|\d{8})\b")


def mask_account_and_sort_codes(text: str) -> str:
    """Mask account numbers and sort codes in the provided text.

    Any sequence that looks like a sort code (six digits, optionally with
    hyphens) or an eight digit account number will be replaced with
    ``****XXXX`` where ``XXXX`` are the last four digits.
    """

    def repl(match: re.Match) -> str:
        digits = re.sub(r"\D", "", match.group(0))
        return "****" + digits[-4:]

    return _MASK_RE.sub(repl, text)


def mask_transaction(tx: 'Transaction') -> 'Transaction':
    """Return a copy of *tx* with sensitive fields masked."""

    tx = normalise(tx)
    return Transaction(
        date=tx.date,
        description=mask_account_and_sort_codes(tx.description),
        amount=tx.amount,
        balance=tx.balance,
    )
