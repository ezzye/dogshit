Feature: Command-line interface
  Scenario: Show config path
    When I run the bankcleanr config command
    Then the exit code is 0

  Scenario: Analyse a PDF statement
    When I run the bankcleanr analyse command with "Redacted bank statements/22b583f5-4060-44eb-a844-945cd612353c (1).pdf"
    Then the exit code is 0
    And the summary file exists
    And the summary contains the disclaimer
    And the terminal output contains the disclaimer

  Scenario: Analyse a PDF statement to PDF output
    When I run the bankcleanr analyse command with "Redacted bank statements/22b583f5-4060-44eb-a844-945cd612353c (1).pdf" to "summary.pdf"
    Then the exit code is 0
    And the summary file exists
    And the PDF summary contains the disclaimer

  Scenario: Analyse a PDF statement with the pdf option
    When I run the bankcleanr analyse command with "Redacted bank statements/22b583f5-4060-44eb-a844-945cd612353c (1).pdf" with pdf "extra.pdf"
    Then the exit code is 0
    And the summary file exists
    And the PDF summary contains the disclaimer

  Scenario: Show terminal output
    When I run the bankcleanr analyse command with "Redacted bank statements/22b583f5-4060-44eb-a844-945cd612353c (1).pdf" with terminal output
    Then the exit code is 0
    And the terminal output contains the disclaimer once

  Scenario: Show savings summary in terminal output
    When I run the bankcleanr analyse command with "Redacted bank statements/22b583f5-4060-44eb-a844-945cd612353c (1).pdf" with terminal output
    Then the exit code is 0
    And the terminal output shows savings

  Scenario: Analyse a PDF statement to PDF output with terminal output
    When I run the bankcleanr analyse command with "Redacted bank statements/22b583f5-4060-44eb-a844-945cd612353c (1).pdf" to "combo.pdf" with terminal output
    Then the exit code is 0
    And the summary file exists
    And the terminal output contains the disclaimer once
    And the PDF summary contains the disclaimer

  Scenario: Analyse a directory of PDF statements
    When I run the bankcleanr analyse command with "Redacted bank statements"
    Then the exit code is 0
    And the summary file exists
    And the summary contains the disclaimer
    And the terminal output contains the disclaimer

  Scenario: Analyse a directory of PDF statements to PDF output
    When I run the bankcleanr analyse command with "Redacted bank statements" with pdf "dir_summary.pdf"
    Then the exit code is 0
    And the summary file exists
    And the PDF summary contains the disclaimer

  Scenario: Analyse a PDF statement with the outdir option
    When I run the bankcleanr analyse command with "Redacted bank statements/22b583f5-4060-44eb-a844-945cd612353c (1).pdf" in outdir "results"
    Then the exit code is 0
    And the summary file exists
    And the summary contains the disclaimer

  Scenario: Analyse a PDF statement with LLM classification
    Given an API key is configured
    When I run the bankcleanr analyse command with "Redacted bank statements/22b583f5-4060-44eb-a844-945cd612353c (1).pdf"
    Then the exit code is 0
    And the summary actions include "Investigate"

  Scenario: Analyse a PDF statement with verbose output
    When I run the bankcleanr analyse command with "Redacted bank statements/22b583f5-4060-44eb-a844-945cd612353c (1).pdf" with verbose output
    Then the exit code is 0
    And the terminal output contains "22b583f5-4060-44eb-a844-945cd612353c (1).pdf"

  Scenario: Progress messages are displayed
    When I run the bankcleanr analyse command with "Redacted bank statements/22b583f5-4060-44eb-a844-945cd612353c (1).pdf" with terminal output
    Then the exit code is 0
    And the terminal output contains "Loaded"
    And the terminal output contains "Classifying"
    And the terminal output contains "Analysis complete"
