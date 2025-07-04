from typing import List, Mapping
from pathlib import Path
from .pdf import generic


def load_transactions(path: str) -> List[Mapping]:
    """Dispatch to the appropriate parser based on file type."""
    if path.lower().endswith(".pdf"):
        return generic.parse_pdf(path)
    raise ValueError("Unsupported file type")


def load_from_path(path: str) -> List[Mapping]:
    """Load transactions from a file or directory of PDF files."""
    p = Path(path)
    if p.is_dir():
        transactions: List[Mapping] = []
        for pdf in sorted(p.glob("*.pdf")):
            transactions.extend(load_transactions(str(pdf)))
        return transactions
    return load_transactions(str(p))
