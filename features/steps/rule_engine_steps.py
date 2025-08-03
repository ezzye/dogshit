import os
from behave import when, then

from features.steps.backend_api_steps import _setup_client, app


@when('I create a user rule with label "{label}" pattern "{pattern}" priority {priority:d} for user {user_id:d}')
def when_create_user_rule(context, label, pattern, priority, user_id):
    if not hasattr(context, "client"):
        _setup_client(context)
    context.client.post(
        "/rules",
        json={"user_id": user_id, "label": label, "pattern": pattern, "priority": priority},
    )
    context.user_id = user_id


@when('I classify with user id {user_id:d}')
def when_classify(context, user_id):
    resp = context.client.post(
        "/classify", json={"job_id": context.job_id, "user_id": user_id}
    )
    context.classification = resp.json()


@then('the classification label is "{label}"')
def then_classification_label(context, label):
    assert context.classification["label"] == label
    context.client.close()
    app.dependency_overrides.clear()
    os.environ.pop("AUTH_BYPASS", None)
