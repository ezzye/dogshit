from __future__ import annotations

from typing import Dict, List
from datetime import datetime
from decimal import Decimal

from ..signature import normalise_signature


class PlaceholderParser:
    """Parser used for tests and as an example."""

    def parse(self, pdf_path: str) -> List[Dict[str, str | None]]:  # noqa: D401
        return [
            {
                "date": datetime.strptime("01 Jan 2024", "%d %b %Y").date().isoformat(),
                "description": "placeholder",
                "amount": f"{Decimal('0.00'):+.2f}",
                "balance": f"{Decimal('0.00'):+.2f}",
                "merchant_signature": normalise_signature("placeholder"),
                "type": "credit",
            }
        ]


BANK = "placeholder"
Parser = PlaceholderParser

__all__ = ["PlaceholderParser", "Parser", "BANK"]
