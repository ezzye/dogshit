"""High level extraction helpers."""
from __future__ import annotations

from typing import Dict, List

from .parsers import PARSER_REGISTRY


def extract_transactions(
    pdf_path: str, bank: str = "barclays"
) -> List[Dict[str, str | None]]:
    """Extract transactions from a PDF statement using the configured parser."""
    parser_cls = PARSER_REGISTRY[bank]
    parser = parser_cls()
    return parser.parse(pdf_path)
