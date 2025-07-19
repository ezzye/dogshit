Feature: LLM classification
  Scenario: Fallback to OpenAI adapter for unknown items
    Given transactions requiring LLM
    And the OpenAI adapter is mocked to return "coffee"
    When I classify transactions with the LLM
    Then the LLM labels are
      | label   |
      | spotify |
    | coffee  |

  Scenario: Fallback to Mistral adapter for unknown items
    Given transactions requiring LLM
    And the Mistral adapter is mocked to return "coffee"
    When I classify transactions with the LLM
    Then the LLM labels are
      | label   |
      | spotify |
      | coffee  |

  Scenario: Account details are masked before sending to the LLM
    Given a transaction containing account details
    When I classify the transaction with a capture adapter
    Then the adapter received the masked transaction

  Scenario: OpenAI adapter throttles concurrent requests
    Given 20 transactions requiring LLM
    And the OpenAI API is replaced with a counting stub
    When I classify transactions with the throttled adapter
    Then no more than 5 concurrent requests were sent

  Scenario: Learned patterns are applied immediately
    Given an empty heuristics file
    And a transaction "Coffee shop"
    And the OpenAI adapter is mocked to return "coffee"
    When I classify transactions with the LLM accepting new patterns
    Then the LLM labels are
      | label |
      | coffee |
