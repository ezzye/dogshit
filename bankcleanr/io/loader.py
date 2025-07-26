from typing import List, Mapping
from pathlib import Path
from .pdf import generic, barclays, lloyds
import pdfplumber


def load_transactions(path: str) -> List[Mapping]:
    """Dispatch to the appropriate parser based on file type."""
    if path.lower().endswith(".pdf"):
        try:
            with pdfplumber.open(path) as pdf:
                text = (pdf.pages[0].extract_text() or "").lower()
        except Exception:
            text = ""

        if "barclays" in text:
            return barclays.parse_pdf(path)
        if "lloyds" in text:
            return lloyds.parse_pdf(path)

        return generic.parse_pdf(path)
    raise ValueError("Unsupported file type")


def load_from_path(path: str, *, verbose: bool = False) -> List[Mapping]:
    """Load transactions from a file or directory of PDF files.

    If ``verbose`` is ``True`` the path of each processed PDF file will be
    printed to stdout before parsing.
    """
    p = Path(path)
    if p.is_dir():
        transactions: List[Mapping] = []
        for pdf in sorted(p.glob("*.pdf")):
            if verbose:
                print(str(pdf))
            transactions.extend(load_transactions(str(pdf)))
        return transactions
    if verbose:
        print(str(p))
    return load_transactions(str(p))
