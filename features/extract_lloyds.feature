Feature: Lloyds PDF extraction
  Scenario: CLI extracts transactions to JSONL
    Given a sample lloyds statement
    When I run the lloyds extractor
    Then a JSONL file with 2 transactions is created
