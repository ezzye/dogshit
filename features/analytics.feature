Feature: Analytics functions
  Scenario: Totals exclude income
    Given recommendations including income
    When I total recommendations by type
    Then income amounts are excluded from totals
