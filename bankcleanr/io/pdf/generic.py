"""Generic PDF statement parser."""

from __future__ import annotations

import re
from typing import List, Mapping

from bankcleanr.transaction import Transaction

import pdfplumber

LINE_RE = re.compile(
    r"^(?P<date>\d{1,2} \w+)\s+(?P<description>.+?)\s+(?P<amount>-?\d+\.\d{2})(?:\s+(?P<balance>-?\d+\.\d{2}))?$"
)


def _parse_lines(lines: List[str]) -> List[Transaction]:
    """Parse lines of text into Transaction objects."""
    rows = []
    for line in lines:
        match = LINE_RE.match(line.strip())
        if match:
            data = match.groupdict()
            rows.append(
                Transaction(
                    date=data.get("date", ""),
                    description=data.get("description", ""),
                    amount=data.get("amount", ""),
                    balance=data.get("balance", ""),
                )
            )
    return rows


def parse_pdf(path: str) -> List[Transaction]:
    """Parse a bank statement PDF into transactions."""
    transactions: List[Transaction] = []

    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                parsed_rows: List[Transaction] = []
                if table and len(table) > 1:
                    header, *body = table
                    for row in body:
                        if len(row) >= 4:
                            parsed_rows.append(
                                Transaction(
                                    date=row[0].strip(),
                                    description=row[1].strip(),
                                    amount=row[2].strip(),
                                    balance=row[3].strip() if len(row) > 3 else "",
                                )
                            )
                    accuracy = len(parsed_rows) / (len(body) or 1)
                    if accuracy < 0.8:
                        parsed_rows = _parse_lines(page.extract_text().splitlines())
                else:
                    parsed_rows = _parse_lines(page.extract_text().splitlines())

                transactions.extend(parsed_rows)
    except Exception:
        transactions = []

    if not transactions:
        try:
            from . import ocr_fallback
            fallback_rows = ocr_fallback.parse_pdf(path)
            transactions = [
                row if isinstance(row, Transaction) else Transaction.from_mapping(row)
                for row in fallback_rows
            ]
        except Exception:
            transactions = []

    return transactions

