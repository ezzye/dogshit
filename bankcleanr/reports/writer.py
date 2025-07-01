from pathlib import Path
import csv
from typing import Iterable, Mapping
from dataclasses import asdict, is_dataclass
from .disclaimers import GLOBAL_DISCLAIMER


def write_summary(transactions: Iterable, output: str) -> Path:
    """Write a minimal CSV summary including the disclaimer."""
    path = Path(output)
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "description", "amount", "balance"])
        for tx in transactions:
            if is_dataclass(tx):
                tx = asdict(tx)
            writer.writerow([
                tx.get("date"),
                tx.get("description"),
                tx.get("amount"),
                tx.get("balance"),
            ])
        writer.writerow([])
        writer.writerow([GLOBAL_DISCLAIMER])
    return path
