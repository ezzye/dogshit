import os
import pytest

from backend.llm_adapter import OpenAIAdapter


@pytest.mark.skipif(not os.getenv("RUN_LLM_E2E"), reason="RUN_LLM_E2E not set")
def test_openai_e2e():
    adapter = OpenAIAdapter()
    out = adapter.classify(["hello"], job_id=1)
    assert isinstance(out, list)
    assert out[0]["label"]
