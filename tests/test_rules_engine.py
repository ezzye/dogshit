from datetime import datetime, timedelta

from rules.engine import Rule, merge_rules, evaluate


def _base_rule(**kwargs):
    base = {
        "scope": "global",
        "priority": 1,
        "version": 1,
        "provenance": "system",
        "confidence": 1.0,
        "match": {"type": "contains", "pattern": "x", "fields": ["description"]},
        "action": {"label": "x", "category": "misc"},
    }
    base.update(kwargs)
    return Rule(**base)


def test_user_rule_overrides_global():
    g = [_base_rule(match={"type": "contains", "pattern": "coffee", "fields": ["description"]}, action={"label": "coffee", "category": "drink"})]
    u = [Rule(scope="user", owner_user_id="1", priority=0, version=1, provenance="user", confidence=1.0,
             match={"type": "contains", "pattern": "coffee", "fields": ["description"]},
             action={"label": "coffee", "category": "drink"})]
    merged = merge_rules(g, u)
    assert merged[0].scope == "user"


def test_precedence_priority_confidence_version_updated():
    now = datetime.utcnow()
    earlier = now - timedelta(days=1)
    rules = [
        _base_rule(priority=2, confidence=0.8, match={"type": "contains", "pattern": "a", "fields": ["description"]}, action={"label": "a", "category": "misc"}),
        _base_rule(priority=1, confidence=0.9, match={"type": "contains", "pattern": "a", "fields": ["description"]}, action={"label": "a", "category": "misc"})
    ]
    merged = merge_rules(rules, [])
    assert merged[0].priority == 1

    rules = [
        _base_rule(confidence=0.8, match={"type": "contains", "pattern": "b", "fields": ["description"]}, action={"label": "b", "category": "misc"}),
        _base_rule(confidence=0.9, match={"type": "contains", "pattern": "b", "fields": ["description"]}, action={"label": "b", "category": "misc"})
    ]
    merged = merge_rules(rules, [])
    assert merged[0].confidence == 0.9

    rules = [
        _base_rule(version=1, match={"type": "contains", "pattern": "c", "fields": ["description"]}, action={"label": "c", "category": "misc"}),
        _base_rule(version=2, match={"type": "contains", "pattern": "c", "fields": ["description"]}, action={"label": "c", "category": "misc"})
    ]
    merged = merge_rules(rules, [])
    assert merged[0].version == 2

    rules = [
        _base_rule(updated_at=earlier, match={"type": "contains", "pattern": "d", "fields": ["description"]}, action={"label": "d", "category": "misc"}),
        _base_rule(updated_at=now, match={"type": "contains", "pattern": "d", "fields": ["description"]}, action={"label": "d", "category": "misc"})
    ]
    merged = merge_rules(rules, [])
    assert merged[0].updated_at == now


def test_match_strategies():
    exact_rule = Rule(scope="global", priority=1, version=1, provenance="system", confidence=1.0,
                      match={"type": "exact", "pattern": "Coffee Shop", "fields": ["description"]},
                      action={"label": "exact", "category": "drink"})
    contains_rule = Rule(scope="global", priority=1, version=1, provenance="system", confidence=1.0,
                         match={"type": "contains", "pattern": "coffee", "fields": ["description"]},
                         action={"label": "contains", "category": "drink"})
    regex_rule = Rule(scope="global", priority=1, version=1, provenance="system", confidence=1.0,
                      match={"type": "regex", "pattern": "^coffee", "flags": ["i"], "fields": ["description"]},
                      action={"label": "regex", "category": "drink"})
    signature_rule = Rule(scope="global", priority=1, version=1, provenance="system", confidence=1.0,
                          match={"type": "signature", "pattern": "CoffeeShop", "fields": ["description"]},
                          action={"label": "signature", "category": "drink"})

    assert evaluate({"description": "Coffee Shop"}, [exact_rule]) == "exact"
    assert evaluate({"description": "my coffee"}, [contains_rule]) == "contains"
    assert evaluate({"description": "Coffee beans"}, [regex_rule]) == "regex"
    assert evaluate({"description": "coffee-shop"}, [signature_rule]) == "signature"


def test_field_selection():
    rule = Rule(scope="global", priority=1, version=1, provenance="system", confidence=1.0,
                match={"type": "contains", "pattern": "acme", "fields": ["counterparty"]},
                action={"label": "vendor", "category": "biz"})
    data = {"description": "paycheck", "counterparty": "ACME Corp"}
    assert evaluate(data, [rule]) == "vendor"


def test_evaluate_uses_precedence():
    rules = [
        Rule(scope="global", priority=5, version=1, provenance="system", confidence=1.0,
             match={"type": "contains", "pattern": "shop", "fields": ["description"]},
             action={"label": "low", "category": "misc"}),
        Rule(scope="global", priority=1, version=1, provenance="system", confidence=1.0,
             match={"type": "contains", "pattern": "shop", "fields": ["description"]},
             action={"label": "high", "category": "misc"}),
    ]
    label = evaluate("coffee shop", merge_rules(rules, []))
    assert label == "high"
