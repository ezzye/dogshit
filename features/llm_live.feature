Feature: Live LLM classification
  Scenario: Classify a transaction with OpenAI
    Given a sample transaction "Coffee shop"
    When I classify the transaction with the live "openai" adapter
    Then the returned category is not "unknown"

  Scenario: Classify a transaction with BFL
    Given a sample transaction "Coffee shop"
    When I classify the transaction with the live "bfl" adapter
    Then the returned category is not "unknown"

  Scenario: Classify a transaction with Gemini
    Given a sample transaction "Coffee shop"
    When I classify the transaction with the live "gemini" adapter
    Then the returned category is not "unknown"
