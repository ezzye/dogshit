"""Generic PDF statement parser."""

from __future__ import annotations

import re
from typing import List, Mapping

from bankcleanr.transaction import Transaction

import pdfplumber

LINE_RE = re.compile(
    r"^(?P<date>\d{1,2} \w+)\s+(?P<description>.+?)\s+(?P<amount>-?\d+\.\d{2})(?:\s+(?P<balance>-?\d+\.\d{2}))?$"
)

LINE_IN_OUT_RE = re.compile(
    r"^(?P<date>\d{1,2} \w+)\s+(?P<description>.+?)\s+(?P<money_out>\d+\.\d{2})\s+(?P<money_in>\d+\.\d{2})\s+(?P<balance>-?\d+\.\d{2})$"
)


def _parse_lines(lines: List[str]) -> List[Transaction]:
    """Parse lines of text into Transaction objects."""
    rows = []
    for line in lines:
        text = line.strip()
        match = LINE_IN_OUT_RE.match(text)
        if match:
            data = match.groupdict()
            money_in = data.get("money_in", "")
            money_out = data.get("money_out", "")
            if money_in and money_in != "0.00":
                amount = money_in
            else:
                amount = f"-{money_out.lstrip('-')}" if money_out else ""
            rows.append(
                Transaction(
                    date=data.get("date", ""),
                    description=data.get("description", ""),
                    amount=amount,
                    balance=data.get("balance", ""),
                )
            )
            continue
        match = LINE_RE.match(text)
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
                    header_clean = [h.strip().lower() if h else "" for h in header]
                    has_in_out = "money in" in header_clean and "money out" in header_clean
                    for row in body:
                        if len(row) >= 4:
                            if has_in_out:
                                idx_date = header_clean.index("date") if "date" in header_clean else 0
                                idx_desc = header_clean.index("description") if "description" in header_clean else 1
                                idx_out = header_clean.index("money out")
                                idx_in = header_clean.index("money in")
                                idx_balance = header_clean.index("balance") if "balance" in header_clean else 4
                                money_in = row[idx_in].strip() if idx_in < len(row) else ""
                                money_out = row[idx_out].strip() if idx_out < len(row) else ""
                                amount = ""
                                if money_in:
                                    amount = money_in.strip()
                                elif money_out:
                                    mo = money_out.strip().lstrip("+")
                                    amount = f"-{mo.lstrip('-')}" if mo else ""
                                parsed_rows.append(
                                    Transaction(
                                        date=row[idx_date].strip(),
                                        description=row[idx_desc].strip(),
                                        amount=amount,
                                        balance=row[idx_balance].strip() if idx_balance < len(row) else "",
                                    )
                                )
                            else:
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

