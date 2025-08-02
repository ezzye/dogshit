Feature: Backend API
  Scenario: Uploading content tracks job status
    Given the API client
    When I upload text "hello world"
    Then the job status is "pending"

  Scenario: Managing user rules
    Given the API client
    When I create a rule "allow all"
    Then the rules list contains "allow all"
