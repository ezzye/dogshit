Feature: HSBC PDF extraction
  Scenario: CLI extracts transactions to JSONL
    Given a sample hsbc statement
    When I run the hsbc extractor
    Then a JSONL file with 2 transactions is created
