Feature: Directory PDF extraction
  Scenario: CLI extracts transactions from a directory
    Given multiple coop statements
    When I run the coop extractor on the directory
    Then a JSONL file with 34 transactions is created
