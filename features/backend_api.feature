Feature: Backend API
  Scenario: Uploading content tracks job status
    Given the API client
    When I upload text "hello world"
    Then the job status is "uploaded"

  Scenario: Managing user rules
    Given the API client
    When I create a rule "Groceries"
    Then the rules list contains "Groceries"

  Scenario: Downloading with a valid signature
    Given the API client
    When I generate a signed download URL
    Then accessing the URL returns 200

  Scenario: Downloading with an expired signature
    Given the API client
    When I generate an expired signed download URL
    Then accessing the URL returns 403

  Scenario: Rejecting uploads with unsupported content type
    Given the API client
    When I upload with content type "application/json"
    Then the response status is 415

  Scenario: Rejecting uploads over 100 MB
    Given the API client
    When I upload data of size 101 MB
    Then the response status is 413

  Scenario: Generating summaries
    Given the API client
    When I upload text "{\"date\": \"2024-01-01\", \"amount\": \"1\", \"description\": \"a\", \"type\": \"debit\"}"
    And I classify with user id 0
    And I request the summary
    Then the summary response has key "totals"
