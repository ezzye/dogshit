from .base import AbstractAdapter


class MistralAdapter(AbstractAdapter):
    def classify_transactions(self, transactions):
        return ["unknown" for _ in transactions]
