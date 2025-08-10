Feature: Directory PDF extraction
  Scenario: CLI extracts transactions from a directory
    Given multiple barclays statements
    When I run the barclays extractor on the directory
    Then a JSONL file with 4 transactions is created
