
"""OCR-based PDF parsing fallback."""

from __future__ import annotations

from typing import List, Mapping

import pdfplumber
import pytesseract

from .generic import _parse_lines


def parse_pdf(path: str) -> List[Mapping[str, str]]:
    """Extract transactions using OCR when text extraction fails."""
    rows: List[Mapping[str, str]] = []
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                image = page.to_image(resolution=300).original
                text = pytesseract.image_to_string(image)
                rows.extend(_parse_lines(text.splitlines()))
    except (pytesseract.TesseractNotFoundError, Exception):
        # If OCR fails or Tesseract is missing, return empty list
        rows = []
    return rows

