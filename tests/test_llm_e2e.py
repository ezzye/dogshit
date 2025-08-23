import os
import pytest

from backend.llm_adapter import OpenAIAdapter
from backend.database import init_db


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set"
)
def test_openai_e2e():
    init_db()
    adapter = OpenAIAdapter()
    out = adapter.classify(["hello"], job_id=1)
    assert isinstance(out, list)
    assert out[0]["label"].strip(), "label should not be empty"
