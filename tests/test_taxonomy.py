import pytest

from backend.analytics import load_categories, validate_rule_categories
from rules.engine import Action, Match, Rule, load_global_rules


def test_categories_list_structure():
    categories = load_categories()
    assert isinstance(categories, list)
    assert categories and all(isinstance(c, str) for c in categories)


def test_global_rules_categories_in_taxonomy():
    categories = set(load_categories())
    rules = load_global_rules()
    assert {r.action.category for r in rules} <= categories


def test_validate_rule_categories_rejects_unknown():
    rule = Rule(
        scope="global",
        priority=1,
        match=Match(type="contains", pattern="foo", fields=["description"]),
        action=Action(category="Nonexistent"),
    )
    with pytest.raises(ValueError):
        validate_rule_categories([rule])
