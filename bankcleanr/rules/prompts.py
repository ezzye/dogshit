from jinja2 import Template

CATEGORY_PROMPT = Template(
    "Classify the following transaction description: {{ description }}"
)
