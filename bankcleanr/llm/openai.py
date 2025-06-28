from .base import AbstractAdapter


class OpenAIAdapter(AbstractAdapter):
    """Stub adapter for OpenAI API."""

    def classify_transactions(self, transactions):
        return ["unknown" for _ in transactions]
