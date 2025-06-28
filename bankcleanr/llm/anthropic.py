from .base import AbstractAdapter


class AnthropicAdapter(AbstractAdapter):
    def classify_transactions(self, transactions):
        return ["unknown" for _ in transactions]
