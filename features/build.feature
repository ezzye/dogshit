Feature: Build bankcleanr executable
  Scenario: Building from arbitrary directory
    Given a temporary working directory for build
    When I run the bankcleanr build command
    Then a bankcleanr executable is created
