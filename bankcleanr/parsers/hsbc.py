from __future__ import annotations

import re
from typing import Dict, List
from datetime import datetime
from decimal import Decimal

import pdfplumber

from ..pii import mask_pii
from ..signature import normalise_signature

_LINE_RE = re.compile(
    r"^(\d{2} \w{3} \d{4})\s+(.*?)\s+(-?\d+\.\d{2})\s+(-?\d+\.\d{2})$"
)


class HSBCParser:
    """Parse HSBC PDF statements into transactions."""

    def parse(self, pdf_path: str) -> List[Dict[str, str | None]]:
        records: List[Dict[str, str | None]] = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                lines = page.extract_text().split("\n")
                for line in lines:
                    match = _LINE_RE.match(line.strip())
                    if match:
                        date, desc, amount, balance = match.groups()
                        clean_desc = mask_pii(desc.strip())
                        records.append(
                            {
                                "date": datetime.strptime(date, "%d %b %Y").date().isoformat(),
                                "description": clean_desc,
                                "amount": f"{Decimal(amount):+.2f}",
                                "balance": f"{Decimal(balance):+.2f}",
                                "merchant_signature": normalise_signature(clean_desc),
                            }
                        )
        return records


BANK = "hsbc"
Parser = HSBCParser

__all__ = ["HSBCParser", "Parser", "BANK"]
