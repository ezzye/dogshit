Feature: Rule engine
  Scenario: User rule overrides global rule
    Given the API client
    When I create a user rule with label "coffee" pattern "coffee" priority 5 for user 1
    And I upload text "coffee shop"
    And I classify with user id 1
    Then the classification label is "coffee"
