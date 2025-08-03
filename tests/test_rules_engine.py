from datetime import datetime, timedelta

from rules.engine import Rule, merge_rules, evaluate


def test_user_rule_overrides_global():
    g = [Rule(label="coffee", pattern="coffee", priority=1)]
    u = [Rule(label="coffee", pattern="coffee", priority=0, user_id=1)]
    merged = merge_rules(g, u)
    assert merged[0].user_id == 1


def test_precedence_priority_confidence_version_updated():
    now = datetime.utcnow()
    earlier = now - timedelta(days=1)
    rules = [
        Rule(label="a", pattern="a", priority=1, confidence=0.9, version=1, updated_at=earlier),
        Rule(label="a", pattern="a", priority=2, confidence=0.8, version=1, updated_at=now),
    ]
    merged = merge_rules(rules, [])
    assert merged[0].priority == 2

    rules = [
        Rule(label="b", pattern="b", priority=1, confidence=0.8, version=1, updated_at=now),
        Rule(label="b", pattern="b", priority=1, confidence=0.9, version=1, updated_at=earlier),
    ]
    merged = merge_rules(rules, [])
    assert merged[0].confidence == 0.9

    rules = [
        Rule(label="c", pattern="c", priority=1, confidence=0.9, version=2, updated_at=earlier),
        Rule(label="c", pattern="c", priority=1, confidence=0.9, version=1, updated_at=now),
    ]
    merged = merge_rules(rules, [])
    assert merged[0].version == 2

    rules = [
        Rule(label="d", pattern="d", priority=1, confidence=0.9, version=1, updated_at=now),
        Rule(label="d", pattern="d", priority=1, confidence=0.9, version=1, updated_at=earlier),
    ]
    merged = merge_rules(rules, [])
    assert merged[0].updated_at == now


def test_evaluate_uses_precedence():
    rules = [
        Rule(label="low", pattern="shop", priority=1),
        Rule(label="high", pattern="shop", priority=5),
    ]
    label = evaluate("coffee shop", merge_rules(rules, []))
    assert label == "high"
