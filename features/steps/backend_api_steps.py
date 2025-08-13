import tempfile
from pathlib import Path
import json
import os

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool
from behave import given, when, then  # type: ignore[import-untyped]

from backend.app import app
from backend.database import get_session
from backend.signing import generate_signed_url
import backend.llm_adapter as llm_adapter


def _setup_client(context):
    os.environ["AUTH_BYPASS"] = "1"
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)

    def get_session_override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_session_override
    llm_adapter.get_session = get_session_override

    class DummyAdapter(llm_adapter.AbstractAdapter):
        def __init__(self):
            super().__init__("test")

        def _send(self, prompts):
            return {"labels": [("unknown", 0.0)] * len(prompts), "usage": {"total_tokens": 0}}

    dummy_adapter = DummyAdapter()

    def adapter_override():
        return dummy_adapter

    app.dependency_overrides[llm_adapter.get_adapter] = adapter_override
    context.client = TestClient(app)


@given("the API client")
def given_client(context):
    _setup_client(context)


@when('I upload text "{text}"')
def when_upload_text(context, text):
    data = text
    if not text.strip().startswith("{"):
        data = json.dumps({"description": text, "type": "debit"})
    resp = context.client.post(
        "/upload", data=data, headers={"Content-Type": "application/x-ndjson"}
    )
    context.job_id = resp.json()["job_id"]


@then('the job status is "{status}"')
def then_job_status(context, status):
    resp = context.client.get(f"/status/{context.job_id}")
    assert resp.json()["status"] == status
    context.client.close()
    app.dependency_overrides.clear()
    os.environ.pop("AUTH_BYPASS", None)
    os.environ.pop("STORAGE_DIR", None)


@when('I create a rule "{text}"')
def when_create_rule(context, text):
    context.client.post("/rules", json={"label": text, "pattern": text})


@then('the rules list contains "{text}"')
def then_rules_list(context, text):
    resp = context.client.get("/rules")
    rules = [r["label"] for r in resp.json()]
    assert text in rules
    context.client.close()
    app.dependency_overrides.clear()
    os.environ.pop("AUTH_BYPASS", None)
    os.environ.pop("STORAGE_DIR", None)


@when("I generate a signed download URL")
def when_generate_signed_url(context):
    resp = context.client.post(
        "/upload", data="data", headers={"Content-Type": "text/plain"}
    )
    job_id = resp.json()["job_id"]
    storage = Path(tempfile.mkdtemp())
    os.environ["STORAGE_DIR"] = str(storage)
    (storage / f"{job_id}_summary.txt").write_text("result")
    context.url = generate_signed_url(f"/download/{job_id}/summary")


@when("I generate an expired signed download URL")
def when_generate_expired_signed_url(context):
    resp = context.client.post(
        "/upload", data="data", headers={"Content-Type": "text/plain"}
    )
    job_id = resp.json()["job_id"]
    storage = Path(tempfile.mkdtemp())
    os.environ["STORAGE_DIR"] = str(storage)
    (storage / f"{job_id}_summary.txt").write_text("result")
    context.url = generate_signed_url(f"/download/{job_id}/summary", expires_in=-1)


@then("accessing the URL returns {status:d}")
def then_accessing_url_returns(context, status):
    resp = context.client.get(context.url)
    assert resp.status_code == status
    context.client.close()
    app.dependency_overrides.clear()
    os.environ.pop("AUTH_BYPASS", None)
    os.environ.pop("STORAGE_DIR", None)


@when('I upload with content type "{content_type}"')
def when_upload_with_content_type(context, content_type):
    context.response = context.client.post(
        "/upload", data="hello", headers={"Content-Type": content_type}
    )


@when("I upload data of size {size:d} MB")
def when_upload_data_of_size(context, size):
    data = b"x" * (size * 1024 * 1024)
    context.response = context.client.post(
        "/upload", data=data, headers={"Content-Type": "text/plain"}
    )


@then("the response status is {status:d}")
def then_response_status(context, status):
    assert context.response.status_code == status
    context.client.close()
    app.dependency_overrides.clear()
    os.environ.pop("AUTH_BYPASS", None)
    os.environ.pop("STORAGE_DIR", None)


@when("I request the summary")
def when_request_summary(context):
    resp = context.client.get(f"/summary/{context.job_id}")
    context.summary = resp.json()


@then('the summary response has key "{key}"')
def then_summary_has_key(context, key):
    assert key in context.summary
    context.client.close()
    app.dependency_overrides.clear()
    os.environ.pop("AUTH_BYPASS", None)
    os.environ.pop("STORAGE_DIR", None)
