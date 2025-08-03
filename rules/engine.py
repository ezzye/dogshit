import json
import re
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

from pydantic import BaseModel, Field


class Rule(BaseModel):
    label: str
    pattern: str
    priority: int = 0
    confidence: float = 1.0
    version: int = 1
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[int] = None


def load_global_rules(path: Optional[str] = None) -> List[Rule]:
    """Load global rules from heuristic_rule_v1.json."""
    if path is None:
        path = Path(__file__).with_name("heuristic_rule_v1.json")
    else:
        path = Path(path)
    with path.open() as f:
        data = json.load(f)
    return [Rule(**item) for item in data]


def _precedence_key(rule: Rule):
    # higher values should come first
    return (rule.priority, rule.confidence, rule.version, rule.updated_at)


def merge_rules(global_rules: Iterable[Rule], user_rules: Iterable[Rule]) -> List[Rule]:
    """Merge global and user rules applying precedence and overrides."""
    combined: dict[tuple[str, str], Rule] = {}
    for rule in global_rules:
        key = (rule.label, rule.pattern)
        existing = combined.get(key)
        if not existing or _precedence_key(rule) > _precedence_key(existing):
            combined[key] = rule
    for rule in user_rules:
        key = (rule.label, rule.pattern)
        # user rule always overrides
        combined[key] = rule
    return sorted(combined.values(), key=_precedence_key, reverse=True)


def evaluate(text: str, rules: Iterable[Rule]) -> Optional[str]:
    for rule in sorted(rules, key=_precedence_key, reverse=True):
        if re.search(rule.pattern, text, flags=re.IGNORECASE):
            return rule.label
    return None
