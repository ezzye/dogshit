Feature: Backend API
  Scenario: Upload and summarise transactions
    Given an authenticated client
    When I POST two transactions to "/upload"
    Then the summary endpoint reports 2 transactions
