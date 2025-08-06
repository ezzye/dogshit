import pytest
from sqlmodel import SQLModel, Session, create_engine, select
from sqlalchemy.pool import StaticPool

from backend.llm_adapter import AbstractAdapter, DailyCostTracker
from backend.models import LLMCost


class DummyAdapter(AbstractAdapter):
    def __init__(self, responses, fail_times=0):
        super().__init__("test-model", batch_size=2, max_retries=3)
        self.responses = responses
        self.fail_times = fail_times
        self.calls = 0

    def _send(self, prompts):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise RuntimeError("boom")
        labels = []
        tokens = 0
        for p in prompts:
            data = self.responses[p]
            labels.append((data["label"], data["confidence"]))
            tokens += data["tokens"]
        return {"labels": labels, "usage": {"prompt_tokens": tokens, "completion_tokens": 0}}


@pytest.fixture
def engine(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def get_session_override():
        with Session(engine) as session:
            yield session

    monkeypatch.setattr("backend.llm_adapter.get_session", get_session_override)
    return engine


def test_retries(engine, monkeypatch):
    tracker = DailyCostTracker(limit=1.0)
    monkeypatch.setattr("backend.llm_adapter.cost_tracker", tracker)
    adapter = DummyAdapter({"a": {"label": "x", "confidence": 1.0, "tokens": 10}}, fail_times=1)
    out = adapter.classify(["a"], job_id=1)
    assert out[0]["label"] == "x"
    assert adapter.calls == 2


def test_records_cost(engine, monkeypatch):
    tracker = DailyCostTracker(limit=1.0)
    monkeypatch.setattr("backend.llm_adapter.cost_tracker", tracker)
    adapter = DummyAdapter({"a": {"label": "x", "confidence": 1.0, "tokens": 10}})
    adapter.classify(["a"], job_id=1)
    with Session(engine) as session:
        entry = session.exec(select(LLMCost)).one()
        assert entry.job_id == 1
        assert entry.tokens_in == 10
        assert entry.tokens_out == 0
        assert entry.estimated_cost_gbp == pytest.approx(
            10 / 1000 * adapter.price_per_1k_tokens_gbp
        )


def test_cost_limit(engine, monkeypatch):
    tracker = DailyCostTracker(limit=0.0001)
    monkeypatch.setattr("backend.llm_adapter.cost_tracker", tracker)
    adapter = DummyAdapter({"a": {"label": "x", "confidence": 1.0, "tokens": 1000}})
    with pytest.raises(RuntimeError):
        adapter.classify(["a"], job_id=1)
    with Session(engine) as session:
        assert session.exec(select(LLMCost)).first() is None
