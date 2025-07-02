from jinja2 import Template

CATEGORY_PROMPT = Template(
    """
    Classify the following transaction description and respond with JSON.

    Required keys:
      "category"            - short label for the merchant
      "reasons_to_cancel"   - list explaining why a user might cancel
      "checklist"           - step-by-step cancellation checklist

    Transaction: {{ description }}
    """
)
