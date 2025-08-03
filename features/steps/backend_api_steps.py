import os
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool
from behave import given, when, then

from backend.app import app
from backend.database import get_session
from backend.signing import generate_signed_url


def _setup_client(context):
    os.environ["AUTH_BYPASS"] = "1"
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)

    def get_session_override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_session_override
    context.client = TestClient(app)


@given("the API client")
def given_client(context):
    _setup_client(context)


@when('I upload text "{text}"')
def when_upload_text(context, text):
    resp = context.client.post("/upload", data=text)
    context.job_id = resp.json()["job_id"]


@then('the job status is "{status}"')
def then_job_status(context, status):
    resp = context.client.get(f"/status/{context.job_id}")
    assert resp.json()["status"] == status
    context.client.close()
    app.dependency_overrides.clear()
    os.environ.pop("AUTH_BYPASS", None)


@when('I create a rule "{text}"')
def when_create_rule(context, text):
    context.client.post("/rules", json={"rule_text": text})


@then('the rules list contains "{text}"')
def then_rules_list(context, text):
    resp = context.client.get("/rules")
    rules = [r["rule_text"] for r in resp.json()]
    assert text in rules
    context.client.close()
    app.dependency_overrides.clear()
    os.environ.pop("AUTH_BYPASS", None)


@when("I generate a signed download URL")
def when_generate_signed_url(context):
    resp = context.client.post("/upload", data="data")
    job_id = resp.json()["job_id"]
    context.url = generate_signed_url(f"/download/{job_id}/summary")


@when("I generate an expired signed download URL")
def when_generate_expired_signed_url(context):
    resp = context.client.post("/upload", data="data")
    job_id = resp.json()["job_id"]
    context.url = generate_signed_url(f"/download/{job_id}/summary", expires_in=-1)


@then("accessing the URL returns {status:d}")
def then_accessing_url_returns(context, status):
    resp = context.client.get(context.url)
    assert resp.status_code == status
    context.client.close()
    app.dependency_overrides.clear()
    os.environ.pop("AUTH_BYPASS", None)
