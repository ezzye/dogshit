from typing import List, Mapping
from .pdf import generic


def load_transactions(path: str) -> List[Mapping]:
    """Dispatch to the appropriate parser based on file type."""
    if path.lower().endswith(".pdf"):
        return generic.parse_pdf(path)
    raise ValueError("Unsupported file type")
