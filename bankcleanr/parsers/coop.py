from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal
from typing import Dict, List

import pdfplumber

from ..pii import mask_pii
from ..signature import normalise_signature

# Real Co-op statements often omit the year on each line and sometimes
# collapse columns when converted to text.  The parser therefore looks for
# date tokens and numeric values within each line rather than relying on a
# strict column layout.
_MONTH_RE = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
_DATE_RE = re.compile(rf"\d{{1,2}} {_MONTH_RE}", re.IGNORECASE)
_STATEMENT_DATE_RE = re.compile(
    rf"Statement date\s+\d{{1,2}} {_MONTH_RE} (\d{{2,4}})", re.IGNORECASE
)


class CoopParser:
    """Parse Co-op PDF statements into transactions."""

    def parse(self, pdf_path: str) -> List[Dict[str, str | None]]:  # noqa: D401
        records: List[Dict[str, str | None]] = []
        with pdfplumber.open(pdf_path) as pdf:
            year: int | None = None
            for page in pdf.pages:
                lines = page.extract_text().split("\n")
                if year is None:
                    for line in lines:
                        m = _STATEMENT_DATE_RE.search(line)
                        if m:
                            y = m.group(1)
                            year = int(y) if len(y) == 4 else 2000 + int(y)
                            break
                for line in lines:
                    if "Statement number" in line:
                        continue
                    if "Statement date" in line:
                        # retain any transaction details that may follow the
                        # statement date header
                        line = _STATEMENT_DATE_RE.sub("", line)
                    m = _DATE_RE.search(line)
                    if not m or year is None:
                        continue
                    date_token = m.group(0)
                    remainder = line[m.end() :].strip()
                    numbers = re.findall(r"\d+\.\d{2}", remainder)
                    if not numbers:
                        continue
                    description = remainder
                    for num in numbers:
                        description = description.replace(num, "")
                    description = description.strip()
                    if description.upper().startswith("BROUGHT FORWARD"):
                        continue
                    try:
                        date = datetime.strptime(
                            f"{date_token} {year}", "%d %B %Y"
                        ).date()
                    except ValueError:
                        date = datetime.strptime(
                            f"{date_token} {year}", "%d %b %Y"
                        ).date()
                    amount = Decimal(numbers[0])
                    if len(numbers) > 1:
                        balance = Decimal(numbers[1])
                        sign = 1
                    else:
                        balance = None
                        sign = -1
                    clean_desc = mask_pii(description)
                    tx_amount = amount * sign
                    records.append(
                        {
                            "date": date.isoformat(),
                            "description": clean_desc,
                            "amount": f"{tx_amount:+.2f}",
                            "balance": f"{balance:+.2f}" if balance is not None else None,
                            "merchant_signature": normalise_signature(clean_desc),
                            "type": "credit" if tx_amount > 0 else "debit",
                        }
                    )
        return records


BANK = "coop"
Parser = CoopParser

__all__ = ["CoopParser", "Parser", "BANK"]
