from .base import AbstractAdapter


class LocalOllamaAdapter(AbstractAdapter):
    def classify_transactions(self, transactions):
        return ["unknown" for _ in transactions]
