Feature: Co-op PDF extraction
  Scenario: CLI extracts transactions to JSONL
    Given a sample coop statement
    When I run the coop extractor
    Then a JSONL file with 9 transactions is created
