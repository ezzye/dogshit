"""PDF statement parsers."""
from __future__ import annotations

import re
from typing import Dict, List, Type

import pdfplumber

from ..pii import mask_pii

_LINE_RE = re.compile(
    r"^(\d{2} \w{3} \d{4})\s+(.*?)\s+(-?\d+\.\d{2})\s+(-?\d+\.\d{2})$"
)


class BarclaysParser:
    """Parse Barclays PDF statements into transactions."""

    def parse(self, pdf_path: str) -> List[Dict[str, str | None]]:
        records: List[Dict[str, str | None]] = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                lines = page.extract_text().split("\n")
                for line in lines:
                    match = _LINE_RE.match(line.strip())
                    if match:
                        date, desc, amount, balance = match.groups()
                        records.append(
                            {
                                "date": date,
                                "description": mask_pii(desc.strip()),
                                "amount": amount,
                                "balance": balance,
                            }
                        )
        return records


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


PARSER_REGISTRY: Dict[str, Type] = {
    "barclays": BarclaysParser,
    "placeholder": PlaceholderParser,
}

__all__ = ["BarclaysParser", "PlaceholderParser", "PARSER_REGISTRY"]
