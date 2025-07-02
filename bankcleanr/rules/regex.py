import re

PATTERNS = {
    "spotify": re.compile(r"spotify", re.I),
    "netflix": re.compile(r"netflix", re.I),
    "icloud": re.compile(r"icloud", re.I),
    "amazon prime": re.compile(r"amazon\s+prime", re.I),
    "dropbox": re.compile(r"dropbox", re.I),
}

def classify(description: str) -> str:
    """Return label if description matches a known pattern."""
    for label, pattern in PATTERNS.items():
        if pattern.search(description):
            return label
    return "unknown"
