import re

PATTERNS = {
    "spotify": re.compile(r"spotify", re.I),
    "netflix": re.compile(r"netflix", re.I),
}

def classify(description: str) -> str:
    """Return label if description matches a known pattern."""
    for label, pattern in PATTERNS.items():
        if pattern.search(description):
            return label
    return "unknown"
