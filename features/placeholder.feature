Feature: Placeholder PDF extraction
  Scenario: CLI uses placeholder parser
    Given a sample placeholder statement
    When I run the placeholder extractor
    Then a JSONL file with 1 transactions is created
