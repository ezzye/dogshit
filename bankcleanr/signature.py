"""Utilities for normalising merchant signatures."""

from __future__ import annotations

import re
import string
import unicodedata
from typing import Iterable

_PREFIXES: tuple[str, ...] = (
    "pos",
    "card",
    "payment",
    "purchase",
    "dd",
    "so",
    "sto",
    "tfr",
)

_SUFFIXES: tuple[str, ...] = (
    "uk",
    "gb",
    "co",
    "ltd",
)


def _strip_diacritics(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return normalized.encode("ascii", "ignore").decode("ascii")


def _remove_tokens(text: str, tokens: Iterable[str], *, prefix: bool) -> str:
    for token in tokens:
        if prefix and text.startswith(token + " "):
            text = text[len(token) + 1 :]
        elif not prefix and text.endswith(" " + token):
            text = text[: -(len(token) + 1)]
    return text


def _trim_trailing_digits(text: str, *, min_length: int = 5) -> str:
    tokens = text.split()
    while tokens and tokens[-1].isdigit() and len(tokens[-1]) >= min_length:
        tokens.pop()
    return " ".join(tokens)


def normalise_signature(text: str) -> str:
    """Return a normalised merchant signature.

    The normalisation aims to make similar merchant descriptions map to the
    same signature by applying a number of transforms:

    * lower-case conversion
    * removal of punctuation
    * removal of diacritics
    * collapsing of consecutive whitespace
    * removal of common prefixes/suffixes
    * trimming of dynamic digit sequences
    """

    text = _strip_diacritics(text.lower())
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\s+", " ", text).strip()
    text = _remove_tokens(text, _PREFIXES, prefix=True)
    text = _remove_tokens(text, _SUFFIXES, prefix=False)
    text = _trim_trailing_digits(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


__all__ = ["normalise_signature"]

