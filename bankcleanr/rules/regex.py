import re
from pathlib import Path
import yaml

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
HEURISTICS_PATH = DATA_DIR / "heuristics.yml"


def _load_patterns(path: Path = HEURISTICS_PATH) -> dict[str, re.Pattern]:
    """Load regex patterns from the heuristics YAML file."""
    if path.exists():
        data = yaml.safe_load(path.read_text()) or {}
    else:
        data = {}
    return {label: re.compile(pattern, re.I) for label, pattern in data.items()}


PATTERNS = _load_patterns()


def reload_patterns(path: Path = HEURISTICS_PATH) -> None:
    """Reload PATTERNS from the heuristics file."""
    global PATTERNS
    PATTERNS = _load_patterns(path)


def add_pattern(label: str, pattern: str, path: Path = HEURISTICS_PATH) -> None:
    """Append a new label→pattern mapping to the heuristics file."""
    data = {}
    if path.exists():
        data = yaml.safe_load(path.read_text()) or {}
    data[label] = pattern
    path.write_text(yaml.safe_dump(data))
    PATTERNS[label] = re.compile(pattern, re.I)

def classify(description: str) -> str:
    """Return label if description matches a known pattern."""
    for label, pattern in PATTERNS.items():
        if pattern.search(description):
            return label
    return "unknown"
