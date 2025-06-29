Feature: Command-line interface
  Scenario: Show config path
    When I run the bankcleanr config command
    Then the exit code is 0

  Scenario: Analyse a PDF statement
    When I run the bankcleanr analyse command with "Redacted bank statements/22b583f5-4060-44eb-a844-945cd612353c (1).pdf"
    Then the exit code is 0
    And the summary file exists
    And the summary contains the disclaimer
