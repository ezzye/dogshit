# Rule Learning

The classification engine merges global heuristics with user-defined rules. When `merge_rules` combines rule sets it applies precedence in the following order: priority (lowest first), confidence (highest first), version (highest first) and most recent update time. User rules always override global rules sharing the same pattern.

## Learning new rules

During the `/classify` endpoint, transactions without a matching rule are sent to the LLM. If the model returns a label with confidence ≥ 0.85 and the merchant signature contains at least six alphabetic characters, a new `UserRule` is stored with:

- `version` initialised to `1`
- `provenance` set to `llm`
- `confidence` copied from the model output

When the LLM later produces a higher-confidence result for the same signature (confidence ≥ 0.95 and greater than the existing rule), the rule is updated, its `version` is incremented and `updated_at` refreshed. Learned rules are applied via `evaluate` on subsequent classifications, avoiding additional LLM calls.

## Confidence thresholds

- **0.85** – minimum confidence required to create a new rule
- **0.95** – minimum confidence required to update an existing rule, which must also exceed the current confidence

These thresholds help balance precision with false positives and allow rules to evolve as the model becomes more certain.
