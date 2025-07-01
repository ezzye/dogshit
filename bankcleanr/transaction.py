from dataclasses import dataclass, asdict, is_dataclass
from typing import Mapping, Any

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
