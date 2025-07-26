from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Any

from bankcleanr.transaction import normalise, mask_sensitive_fields


def write_jsonl(transactions: Iterable[Any], output: str) -> Path:
    """Write *transactions* to *output* in JSON Lines format.

    Each transaction is normalised, masked, and dumped as a JSON object
    on a single line.
    """
    path = Path(output)
    with path.open("w") as f:
        for tx in transactions:
            masked = mask_sensitive_fields(normalise(tx))
            json.dump(masked.to_dict(), f)
            f.write("\n")
    return path
