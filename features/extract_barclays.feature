Feature: Barclays PDF extraction
  Scenario: CLI extracts transactions to JSONL
    Given a sample Barclays statement
    When I run the extractor
    Then a JSONL file with 2 transactions is created
