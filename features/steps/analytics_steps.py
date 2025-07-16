from behave import given, when, then
from decimal import Decimal

from bankcleanr.transaction import Transaction
from bankcleanr.recommendation import Recommendation
from bankcleanr.analytics import totals_by_type


@given("recommendations including income")
def recs_with_income(context):
    context.recs = [
        Recommendation(Transaction(date="2024-01-01", description="Spotify", amount="-9.99"), "spotify", "Cancel"),
        Recommendation(Transaction(date="2024-01-02", description="Salary", amount="1000.00"), "salary", "Keep"),
        Recommendation(Transaction(date="2024-01-03", description="Bus", amount="-2.50"), "bus", "Keep"),
    ]


@when("I total recommendations by type")
def total_by_type(context):
    context.totals = totals_by_type(context.recs)


@then("income amounts are excluded from totals")
def check_totals(context):
    assert context.totals["entertainment"] == Decimal("9.99")
    assert context.totals["other"] == Decimal("2.50")
