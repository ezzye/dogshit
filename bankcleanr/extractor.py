"""High level extraction helpers."""
from __future__ import annotations
from typing import List, Dict
from .parsers import BarclaysParser


def extract_transactions(pdf_path: str) -> List[Dict[str, str | None]]:
    """Extract transactions from a Barclays PDF statement."""
    parser = BarclaysParser()
    return parser.parse(pdf_path)
