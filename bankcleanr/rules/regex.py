import re
from typing import Dict

from . import db_store


def _load_patterns() -> Dict[str, re.Pattern]:
    """Load regex patterns from the heuristics database."""
    data = db_store.get_patterns()
    return {label: re.compile(pattern, re.I) for label, pattern in data.items()}


PATTERNS = _load_patterns()


def reload_patterns() -> None:
    """Reload PATTERNS from the database."""
    global PATTERNS
    PATTERNS = _load_patterns()


def add_pattern(label: str, pattern: str) -> None:
    """Store a new heuristic pattern in the database."""
    db_store.add_pattern(label, pattern)
    PATTERNS[label] = re.compile(pattern, re.I)


def classify(description: str) -> str:
    """Return label if description matches a known pattern."""
    for label, pattern in PATTERNS.items():
        if pattern.search(description):
            return label
    return "unknown"
