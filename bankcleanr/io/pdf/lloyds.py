import re
import pdfplumber
from .generic import parse_pdf as generic_parse_pdf, _parse_lines
from bankcleanr.transaction import Transaction

DATE_RE = re.compile(r"^\d{1,2} \w+")

def parse_pdf(path: str):
    """Parse Lloyds statements using header-aware line detection."""
    transactions: list[Transaction] = []
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                lines = page.extract_text().splitlines()
                useful = [ln for ln in lines if DATE_RE.match(ln.strip())]
                transactions.extend(_parse_lines(useful))
    except Exception:
        transactions = []

    if not transactions:
        transactions = generic_parse_pdf(path)

    return transactions
