Feature: LLM classification
  Scenario: Fallback to OpenAI adapter for unknown items
    Given transactions requiring LLM
    And the OpenAI adapter is mocked to return "coffee"
    When I classify transactions with the LLM
    Then the LLM labels are
      | label   |
      | spotify |
      | coffee  |

  Scenario: Account details are masked before sending to the LLM
    Given a transaction containing account details
    When I classify the transaction with a capture adapter
    Then the adapter received the masked transaction
