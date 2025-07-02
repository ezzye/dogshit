from behave import when, then

from bankcleanr.llm import PROVIDERS
from bankcleanr import recommendation


@when("I generate recommendations")
def generate_recommendations(context):
    context.recommendations = recommendation.recommend_transactions(context.txs, provider="openai")
    if hasattr(context, "original"):
        PROVIDERS["openai"] = context.original


@then("the recommended actions are")
def check_actions(context):
    expected = [row[0] for row in context.table.rows]
    actions = [rec.action for rec in context.recommendations]
    assert actions == expected


@then("the recommendation categories are")
def check_categories(context):
    expected = [row[0] for row in context.table.rows]
    categories = [rec.category for rec in context.recommendations]
    assert categories == expected


@then("the first recommendation includes cancellation info")
def first_has_info(context):
    assert context.recommendations[0].info is not None
    assert "url" in context.recommendations[0].info
