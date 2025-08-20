from behave import given, when, then  # type: ignore[import-untyped]

from features.steps.backend_api_steps import _setup_client, app
from backend.llm_adapter import AbstractAdapter
from backend.app import get_adapter_dependency


@given('a fake adapter returning label "{label}" with confidence {conf:f}')
def given_fake_adapter(context, label, conf):
    class FakeAdapter(AbstractAdapter):
        def __init__(self):
            super().__init__("test-model")
            self.calls = 0

        def _send(self, prompts):
            self.calls += 1
            return {"labels": [(label, conf)] * len(prompts), "usage": {"total_tokens": 0}}

    if not hasattr(context, "client"):
        _setup_client(context)
    context.fake_adapter = FakeAdapter()
    context.preserve_client = True

    def adapter_override():
        return context.fake_adapter

    app.dependency_overrides[get_adapter_dependency] = adapter_override


@then('the adapter was called {n:d} times')
def then_adapter_called(context, n):
    assert context.fake_adapter.calls == n, context.fake_adapter.calls


@given("the signature cache is cleared")
def given_signature_cache_cleared(context):
    from backend import app as app_module
    app_module.SIGNATURE_CACHE.clear()


@when("I upload NDJSON")
@when("I upload NDJSON:")
def when_upload_ndjson(context):
    if not hasattr(context, "client"):
        _setup_client(context)
    resp = context.client.post(
        "/upload", data=context.text, headers={"Content-Type": "application/x-ndjson"}
    )
    context.job_id = resp.json()["job_id"]


@then('the job status should be "{status}"')
def then_job_status_should_be(context, status):
    resp = context.client.get(f"/status/{context.job_id}")
    assert resp.json()["status"] == status
