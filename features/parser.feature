Feature: PDF parser
  Scenario: Parse minimal PDF
    Given a minimal statement PDF
    When I parse the file
    Then the parser returns two transactions

  Scenario: Parse statement with Money in/out columns
    Given a statement PDF with Money in and out columns
    When I parse the file
    Then the amounts reflect income and expenses
