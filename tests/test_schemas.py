import json
from pathlib import Path

import pytest
from jsonschema import ValidationError, validate


SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"


def load_schema(name: str) -> dict:
    with open(SCHEMAS_DIR / name) as f:
        return json.load(f)


def test_heuristic_rule_valid_example():
    schema = load_schema("heuristic_rule_v1.json")
    example = {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "scope": "user",
        "owner_user_id": "user1",
        "active": True,
        "priority": 1,
        "version": 1,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "provenance": "system",
        "confidence": 0.9,
        "title": "Coffee shops",
        "notes": "Matches coffee merchants",
        "match": {
            "type": "contains",
            "pattern": "coffee",
            "flags": ["i"],
            "fields": ["description"],
        },
        "action": {"category": "Food", "label": "Coffee"},
        "examples": [
            {
                "description": "Starbucks",
                "amount": 3.5,
                "date": "2024-01-02",
            }
        ],
    }

    validate(example, schema)


def test_heuristic_rule_missing_required_field():
    schema = load_schema("heuristic_rule_v1.json")
    example = {
        # Missing 'id'
        "scope": "global",
        "active": True,
        "match": {"type": "exact", "pattern": "coffee", "fields": ["description"]},
        "action": {"category": "Food"},
        "provenance": "system",
        "priority": 1,
        "version": 1,
        "confidence": 0.9,
    }

    with pytest.raises(ValidationError):
        validate(example, schema)


def test_summary_valid_example():
    schema = load_schema("summary_v1.json")
    example = {
        "job_id": "123e4567-e89b-12d3-a456-426614174000",
        "user_id": "user123",
        "period": {"start": "2024-01-01", "end": "2024-01-31"},
        "currency": "GBP",
        "generated_at": "2024-02-01T00:00:00Z",
        "totals": {"income": 1000.0, "expenses": 500.0, "net": 500.0},
        "categories": [
            {
                "name": "Groceries",
                "total": 200.0,
                "count": 5,
                "sample_merchants": ["Tesco"],
            }
        ],
        "recurring": [
            {
                "merchant": "Netflix",
                "cadence": "monthly",
                "avg_amount": 10.0,
                "amount_stddev": 0.0,
                "count": 12,
                "first_seen": "2023-03-01",
                "last_seen": "2024-02-01",
            }
        ],
        "highlights": {"overspending": ["Groceries"], "anomalies": []},
    }

    validate(example, schema)


def test_summary_missing_required_field():
    schema = load_schema("summary_v1.json")
    example = {
        # Missing 'categories'
        "job_id": "123e4567-e89b-12d3-a456-426614174000",
        "user_id": "user123",
        "period": {"start": "2024-01-01", "end": "2024-01-31"},
        "currency": "GBP",
        "totals": {"income": 1000.0, "expenses": 500.0, "net": 500.0},
    }

    with pytest.raises(ValidationError):
        validate(example, schema)

