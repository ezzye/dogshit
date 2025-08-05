import pytest

from backend.llm_adapter import OpenAIAdapter


def test_openai_e2e():
    import os

    if not os.getenv("RUN_LLM_E2E"):
        pytest.skip("RUN_LLM_E2E not set")
    adapter = OpenAIAdapter()
    out = adapter.classify(["hello"], job_id=1)
    assert isinstance(out, list)
    assert out[0]["label"]
