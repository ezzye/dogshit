Feature: Build script
  Scenario: Build and run standalone binary
    When I run the build script
    Then the build succeeds
    And the binary parses the sample PDF to jsonl
    And the jsonl output contains "PAYPAL"
