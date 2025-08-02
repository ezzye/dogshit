"""PDF statement parsers."""
from __future__ import annotations
import re
from typing import List, Dict
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
