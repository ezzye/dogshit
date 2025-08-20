Feature: LLM provider selection
  Scenario: Select Anthropic adapter using environment variable
    Given the environment variable LLM_PROVIDER is set to "anthropic"
    When requesting an LLM adapter
    Then the adapter type is "AnthropicAdapter"

  Scenario: Environment variable cleaned up after scenario
    Then the environment variable LLM_PROVIDER is unset
