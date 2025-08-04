from __future__ import annotations

from typing import Dict, List


class PlaceholderParser:
    """Parser used for tests and as an example."""

    def parse(self, pdf_path: str) -> List[Dict[str, str | None]]:  # noqa: D401
        return [
            {
                "date": "01 Jan 2024",
                "description": "placeholder",
                "amount": "0.00",
                "balance": "0.00",
            }
        ]


BANK = "placeholder"
Parser = PlaceholderParser

__all__ = ["PlaceholderParser", "Parser", "BANK"]
