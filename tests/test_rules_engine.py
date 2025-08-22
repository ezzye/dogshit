from datetime import datetime, timedelta  # for date calculations

from rules.engine import Rule, merge_rules, evaluate


def _base_rule(**kwargs):
    base = {
        "scope": "global",
        "priority": 1,
        "version": 1,
        "provenance": "system",
        "confidence": 1.0,
        "match": {"type": "contains", "pattern": "x", "fields": ["description"]},
        "action": {"label": "x", "category": "Utilities"},
    }
    base.update(kwargs)
    return Rule(**base)


def test_user_rule_overrides_global():
    g = [_base_rule(match={"type": "contains", "pattern": "coffee", "fields": ["description"]}, action={"label": "coffee", "category": "Groceries"})]
    u = [Rule(scope="user", owner_user_id="1", priority=0, version=1, provenance="user", confidence=1.0,
             match={"type": "contains", "pattern": "coffee", "fields": ["description"]},
             action={"label": "coffee", "category": "Groceries"})]
    merged = merge_rules(g, u)
    assert merged[0].scope == "user"


def test_user_rule_overrides_global_with_different_label():
    g = [_base_rule(match={"type": "contains", "pattern": "coffee", "fields": ["description"]},
                    action={"label": "global", "category": "Groceries"})]
    u = [Rule(scope="user", owner_user_id="1", priority=0, version=1, provenance="user", confidence=1.0,
             match={"type": "contains", "pattern": "coffee", "fields": ["description"]},
             action={"label": "user", "category": "Groceries"})]
    merged = merge_rules(g, u)
    assert len(merged) == 1
    assert merged[0].action.label == "user"


def test_precedence_priority_confidence_version_updated():
    now = datetime.utcnow()
    earlier = now - timedelta(days=1)
    rules = [
        _base_rule(priority=2, confidence=0.8, match={"type": "contains", "pattern": "a", "fields": ["description"]}, action={"label": "a", "category": "Utilities"}),
        _base_rule(priority=1, confidence=0.9, match={"type": "contains", "pattern": "a", "fields": ["description"]}, action={"label": "a", "category": "Utilities"})
    ]
    merged = merge_rules(rules, [])
    assert merged[0].priority == 1

    rules = [
        _base_rule(confidence=0.8, match={"type": "contains", "pattern": "b", "fields": ["description"]}, action={"label": "b", "category": "Utilities"}),
        _base_rule(confidence=0.9, match={"type": "contains", "pattern": "b", "fields": ["description"]}, action={"label": "b", "category": "Utilities"})
    ]
    merged = merge_rules(rules, [])
    assert merged[0].confidence == 0.9

    rules = [
        _base_rule(version=1, match={"type": "contains", "pattern": "c", "fields": ["description"]}, action={"label": "c", "category": "Utilities"}),
        _base_rule(version=2, match={"type": "contains", "pattern": "c", "fields": ["description"]}, action={"label": "c", "category": "Utilities"})
    ]
    merged = merge_rules(rules, [])
    assert merged[0].version == 2

    rules = [
        _base_rule(updated_at=earlier, match={"type": "contains", "pattern": "d", "fields": ["description"]}, action={"label": "d", "category": "Utilities"}),
        _base_rule(updated_at=now, match={"type": "contains", "pattern": "d", "fields": ["description"]}, action={"label": "d", "category": "Utilities"})
    ]
    merged = merge_rules(rules, [])
    assert merged[0].updated_at == now


def test_merge_rules_applies_full_precedence():
    now = datetime.utcnow()
    earlier = now - timedelta(days=1)
    rules = [
        _base_rule(priority=2, confidence=0.9, version=1, updated_at=earlier,
                   match={"type": "contains", "pattern": "e", "fields": ["description"]},
                   action={"label": "low", "category": "Utilities"}),
        _base_rule(priority=1, confidence=0.8, version=3, updated_at=earlier,
                   match={"type": "contains", "pattern": "e", "fields": ["description"]},
                   action={"label": "p1_low", "category": "Utilities"}),
        _base_rule(priority=1, confidence=0.9, version=2, updated_at=earlier,
                   match={"type": "contains", "pattern": "e", "fields": ["description"]},
                   action={"label": "p1_high_v2", "category": "Utilities"}),
        _base_rule(priority=1, confidence=0.9, version=2, updated_at=now,
                   match={"type": "contains", "pattern": "e", "fields": ["description"]},
                   action={"label": "winner", "category": "Utilities"}),
    ]
    merged = merge_rules(rules, [])
    assert len(merged) == 1
    assert merged[0].action.label == "winner"


def test_merge_rules_prefers_higher_version():
    rules = [
        _base_rule(version=1,
                   match={"type": "contains", "pattern": "v", "fields": ["description"]},
                   action={"label": "old", "category": "Utilities"}),
        _base_rule(version=2,
                   match={"type": "contains", "pattern": "v", "fields": ["description"]},
                   action={"label": "new", "category": "Utilities"}),
    ]
    merged = merge_rules(rules, [])
    assert len(merged) == 1
    assert merged[0].version == 2
    assert merged[0].action.label == "new"


def test_match_strategies():
    exact_rule = Rule(scope="global", priority=1, version=1, provenance="system", confidence=1.0,
                      match={"type": "exact", "pattern": "Coffee Shop", "fields": ["description"]},
                      action={"label": "exact", "category": "Groceries"})
    contains_rule = Rule(scope="global", priority=1, version=1, provenance="system", confidence=1.0,
                         match={"type": "contains", "pattern": "coffee", "fields": ["description"]},
                         action={"label": "contains", "category": "Groceries"})
    regex_rule = Rule(scope="global", priority=1, version=1, provenance="system", confidence=1.0,
                      match={"type": "regex", "pattern": "^coffee", "flags": ["i"], "fields": ["description"]},
                      action={"label": "regex", "category": "Groceries"})
    signature_rule = Rule(scope="global", priority=1, version=1, provenance="system", confidence=1.0,
                          match={"type": "signature", "pattern": "CoffeeShop", "fields": ["description"]},
                          action={"label": "signature", "category": "Groceries"})

    assert evaluate({"description": "Coffee Shop"}, [exact_rule]) == (
        "exact",
        "Groceries",
    )
    assert evaluate({"description": "my coffee"}, [contains_rule]) == (
        "contains",
        "Groceries",
    )
    assert evaluate({"description": "Coffee beans"}, [regex_rule]) == (
        "regex",
        "Groceries",
    )
    assert evaluate({"description": "coffee-shop"}, [signature_rule]) == (
        "signature",
        "Groceries",
    )


def test_field_selection():
    rule = Rule(scope="global", priority=1, version=1, provenance="system", confidence=1.0,
                match={"type": "contains", "pattern": "acme", "fields": ["counterparty"]},
                action={"label": "vendor", "category": "Fees"})
    data = {"description": "paycheck", "counterparty": "ACME Corp"}
    assert evaluate(data, [rule]) == ("vendor", "Fees")


def test_evaluate_uses_precedence():
    rules = [
        Rule(scope="global", priority=5, version=1, provenance="system", confidence=1.0,
             match={"type": "contains", "pattern": "shop", "fields": ["description"]},
             action={"label": "low", "category": "Utilities"}),
        Rule(scope="global", priority=1, version=1, provenance="system", confidence=1.0,
             match={"type": "contains", "pattern": "shop", "fields": ["description"]},
             action={"label": "high", "category": "Utilities"}),
    ]
    result = evaluate("coffee shop", merge_rules(rules, []))
    assert result == ("high", "Utilities")
