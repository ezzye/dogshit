from jinja2 import Template


CATEGORY_PROMPT = Template(
    """
    Classify the transaction below and respond with JSON.

    Keys:
      "category" - short label for the merchant
      "new_rule" - optional regex pattern to recognise similar transactions

    User heuristics (label: pattern):
    {{ user_heuristics }}

    Global heuristics (label: pattern):
    {{ global_heuristics }}

    Transaction: {{ txn.description }}
    """
)
