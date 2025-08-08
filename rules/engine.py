from pathlib import Path
import json
import re
from datetime import datetime
from typing import Iterable, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent
CATEGORIES_PATH = BASE_DIR / "data" / "taxonomy" / "categories.json"


def load_categories(path: Path = CATEGORIES_PATH) -> List[str]:
    """Load canonical category list from JSON file."""
    with path.open() as f:
        return json.load(f)


class Match(BaseModel):
    type: str
    pattern: str
    flags: List[str] = []
    fields: List[str]


class Action(BaseModel):
    merchant_canonical: Optional[str] = None
    label: Optional[str] = None
    category: str
    subcategory: Optional[str] = None


class Rule(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    scope: str
    owner_user_id: Optional[str] = None
    active: bool = True
    priority: int
    version: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    provenance: str = "system"
    confidence: float = 1.0
    title: Optional[str] = None
    notes: Optional[str] = None
    match: Match
    action: Action


def validate_rule_categories(
    rules: Iterable[Rule], categories: Optional[Iterable[str]] = None
) -> None:
    """Ensure every rule's category is in the sanctioned taxonomy."""
    categories_set = set(categories or load_categories())
    unknown = {r.action.category for r in rules if r.action.category not in categories_set}
    if unknown:
        raise ValueError(f"Unknown categories: {sorted(unknown)}")


def load_global_rules(path: Optional[str] = None) -> List[Rule]:
    """Load global rules from heuristic_rule_v1.json."""
    if path is None:
        path = Path(__file__).with_name("heuristic_rule_v1.json")
    else:
        path = Path(path)
    with path.open() as f:
        data = json.load(f)
    rules = [Rule(**item) for item in data]
    validate_rule_categories(rules)
    return rules


def _precedence_key(rule: Rule):
    return (
        rule.priority,
        -rule.confidence,
        -rule.version,
        -rule.updated_at.timestamp(),
    )


def merge_rules(global_rules: Iterable[Rule], user_rules: Iterable[Rule]) -> List[Rule]:
    """Merge global and user rules applying precedence and overrides."""
    combined: dict[tuple[str, tuple[str, ...]], Rule] = {}
    for rule in global_rules:
        key = (rule.match.pattern, tuple(sorted(rule.match.fields)))
        existing = combined.get(key)
        if not existing or _precedence_key(rule) < _precedence_key(existing):
            combined[key] = rule
    for rule in user_rules:
        key = (rule.match.pattern, tuple(sorted(rule.match.fields)))
        combined[key] = rule
    return sorted(combined.values(), key=_precedence_key)


def norm(s: str) -> str:
    """Normalize a string by stripping non-alphanumeric characters and lowercasing."""
    return re.sub(r"[^A-Za-z0-9]", "", s).lower()


def _match_text(text: str, match: Match) -> bool:
    if match.type == "exact":
        return text == match.pattern
    if match.type == "contains":
        return match.pattern.lower() in text.lower()
    if match.type == "regex":
        flags = 0
        if "i" in match.flags:
            flags |= re.IGNORECASE
        if "m" in match.flags:
            flags |= re.MULTILINE
        return re.search(match.pattern, text, flags=flags) is not None
    if match.type == "signature":
        return norm(text) == norm(match.pattern)
    return False


def evaluate(data: Union[str, dict], rules: Iterable[Rule]) -> Optional[str]:
    if isinstance(data, str):
        record = {"description": data}
    else:
        record = data
    for rule in sorted(rules, key=_precedence_key):
        if not rule.active:
            continue
        for field in rule.match.fields:
            value = record.get(field, "")
            if isinstance(value, str) and _match_text(value, rule.match):
                return rule.action.label or rule.action.category
    return None
