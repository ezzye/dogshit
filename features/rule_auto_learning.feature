Feature: Rule auto-learning
  Scenario: LLM classification creates a persistent rule
    Given the API client
    And a fake adapter returning label "snacks" with confidence 0.9
    When I upload text "Shop 123"
    And I classify with user id 1
    And I classify with user id 1
    Then the classification label is "snacks"
    And the adapter was called 1 times
    And the rules list contains "snacks"
