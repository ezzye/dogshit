Feature: Local heuristics classification
  Scenario: Tag obvious subscriptions
    Given sample transactions
    When I classify transactions locally
    Then the labels are
      | label   |
      | spotify |
      | amazon prime |
      | dropbox |
      | unknown |

  Scenario: Load patterns from YAML
    Given a heuristics file containing
      | label | pattern |
      | gym   | gym membership |
    And a transaction "Monthly gym membership"
    When I classify transactions locally
    Then the labels are
      | label |
      | gym |

  Scenario: Learned patterns persist to backend
    Given an authenticated client
    And an empty heuristics file
    And backend environment variables
    When I learn a pattern labeled "coffee" for "Coffee shop"
    Then the backend has a heuristic labeled "coffee"
