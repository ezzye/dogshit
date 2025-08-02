from dataclasses import dataclass, field
from typing import Any

from bankcleanr.llm.anthropic import AnthropicAdapter
from bankcleanr.transaction import Transaction


@dataclass
class DummyMessage:
    text: str = '{"category": "coffee", "new_rule": ".*COFFEE.*"}'


@dataclass
class DummyResponse:
    content: list[DummyMessage] = field(default_factory=lambda: [DummyMessage()])


class DummyMessages:
    def create(self, *args: Any, **kwargs: Any) -> DummyResponse:  # noqa: D401
        """Return a static response mimicking Anthropic output."""

        return DummyResponse()


@dataclass
class DummyClient:
    messages: DummyMessages = field(default_factory=DummyMessages)


@dataclass
class FailingMessages:
    calls: dict

    def create(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
        """Increment call count and raise an error to simulate failure."""

        self.calls["n"] += 1
        raise RuntimeError("boom")


@dataclass
class FailingClient:
    calls: dict
    messages: FailingMessages = field(init=False)

    def __post_init__(self) -> None:  # noqa: D401
        """Attach a failing messages handler."""

        self.messages = FailingMessages(self.calls)


def test_classify_parses_json():
    adapter = AnthropicAdapter(api_key="dummy")
    adapter.client = DummyClient()
    tx = Transaction(date="2024-01-01", description="Coffee", amount="-1")
    details = adapter.classify_transactions([tx])
    assert details[0]["category"] == "coffee"
    assert details[0]["new_rule"] == ".*COFFEE.*"


def test_retries_then_unknown():
    calls = {"n": 0}

    adapter = AnthropicAdapter(api_key="dummy")
    adapter.client = FailingClient(calls)
    tx = Transaction(date="2024-01-01", description="Coffee", amount="-1")
    details = adapter.classify_transactions([tx])
    assert details == [{"category": "unknown", "new_rule": None}]
    assert calls["n"] == 3

