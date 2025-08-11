Feature: Parse alias
  Scenario: CLI parse command extracts transactions to JSONL
    Given a sample coop statement
    When I parse the coop statement
    Then a JSONL file with 9 transactions is created
