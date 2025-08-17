Feature: Rule auto-learning
  Scenario: LLM classification learns and persists a rule from NDJSON
    Given the API client
    And a fake adapter returning label "Groceries" with confidence 0.9
    When I upload NDJSON:
      """
      {"description": "Corner Shop 123", "type": "debit"}
      """
    Then the job status should be "uploaded"
    When I classify with user id 1
    Then the job status should be "completed"
    And the classification label is "Groceries"
    When I classify with user id 1
    Then the classification label is "Groceries"
    And the rules list contains "Groceries"

  Scenario: Learned rule applied to subsequent upload
    Given the API client
    And a fake adapter returning label "Groceries" with confidence 0.9
    When I upload NDJSON:
      """
      {"description": "Corner Shop 123", "type": "debit"}
      """
    Then the job status should be "uploaded"
    When I classify with user id 1
    Then the job status should be "completed"
    And the classification label is "Groceries"
    Given the signature cache is cleared
    When I upload NDJSON:
      """
      {"description": "Corner Shop 123", "type": "debit"}
      """
    Then the job status should be "uploaded"
    When I classify with user id 1
    Then the classification label is "Groceries"
    And the rules list contains "Groceries"
