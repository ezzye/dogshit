Feature: Local heuristics classification
  Scenario: Tag obvious subscriptions
    Given sample transactions
    When I classify transactions locally
    Then the labels are
      | label   |
      | spotify |
      | unknown |
