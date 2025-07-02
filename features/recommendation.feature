Feature: Recommendation engine
  Scenario: Cancel known merchant using knowledge base
    Given transactions requiring LLM
    And the OpenAI adapter is mocked to return "coffee"
    When I generate recommendations
    Then the recommended actions are
      | action |
      | Cancel |
      | Keep   |
    And the first recommendation includes cancellation info
