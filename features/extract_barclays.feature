Feature: Barclays PDF extraction
  Scenario: CLI extracts transactions to JSONL
    Given a sample barclays statement
    When I run the barclays extractor
    Then a JSONL file with 2 transactions is created
