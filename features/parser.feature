Feature: PDF parser
  Scenario: Parse minimal PDF
    Given a minimal statement PDF
    When I parse the file
    Then the parser returns two transactions
