Feature: Command-line interface
  Scenario: Show config path
    When I run the bankcleanr config command
    Then the exit code is 0
