Feature: Backend API
  Scenario: Upload and summarise transactions
    Given an authenticated client
    When I POST two transactions to "/upload"
    Then the summary endpoint reports 2 transactions

  Scenario: Heuristic editor happy path
    Given an authenticated client
    When I POST two transactions to "/upload"
    And I save a heuristic labeled "coffee" matching "coffee"
    Then the heuristic save response confirms the rule
