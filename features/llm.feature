Feature: LLM classification
  Scenario: Fallback to OpenAI adapter for unknown items
    Given transactions requiring LLM
    And the OpenAI adapter is mocked to return "coffee"
    When I classify transactions with the LLM
    Then the LLM labels are
      | label   |
      | spotify |
      | coffee  |
