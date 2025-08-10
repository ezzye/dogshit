from __future__ import annotations

import re
from typing import Dict, List
from datetime import datetime
from decimal import Decimal

import pdfplumber

from ..pii import mask_pii
from ..signature import normalise_signature

# Co-op statements have separate Moneyout and Moneyin columns
# followed by the running Balance. Amounts are always positive
# and the sign is determined by which column they appear in.
_LINE_RE = re.compile(
    r"^(\d{2} \w{3} \d{4})\s+(.*?)\s+(\d+\.\d{2})\s+(\d+\.\d{2})\s+(\d+\.\d{2})$"
)


class CoopParser:
    """Parse Co-op PDF statements into transactions."""

    def parse(self, pdf_path: str) -> List[Dict[str, str | None]]:
        records: List[Dict[str, str | None]] = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                lines = page.extract_text().split("\n")
                for line in lines:
                    match = _LINE_RE.match(line.strip())
                    if not match:
                        continue
                    date, desc, money_out, money_in, balance = match.groups()
                    money_out_d = Decimal(money_out)
                    money_in_d = Decimal(money_in)
                    amount = money_in_d - money_out_d
                    clean_desc = mask_pii(desc.strip())
                    records.append(
                        {
                            "date": datetime.strptime(date, "%d %b %Y").date().isoformat(),
                            "description": clean_desc,
                            "amount": f"{amount:+.2f}",
                            "balance": f"{Decimal(balance):+.2f}",
                            "merchant_signature": normalise_signature(clean_desc),
                        }
                    )
        return records


BANK = "coop"
Parser = CoopParser

__all__ = ["CoopParser", "Parser", "BANK"]
