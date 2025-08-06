Feature: Rule engine
  Scenario: User rule overrides global rule
    Given the API client
    When I create a user rule with label "coffee" pattern "coffee" priority 5 for user 1
    And I upload text "coffee shop"
    And I classify with user id 1
    Then the classification label is "coffee"

  Scenario: Reject rule with short pattern
     Given the API client
     When I attempt to create a user rule with label "short" pattern "abc" priority 1 for user 1
     Then the response status is 400
