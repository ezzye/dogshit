import time
import pytest

from bankcleanr.llm.utils import probe_adapter
from bankcleanr.llm.base import AbstractAdapter


class DummyAdapter(AbstractAdapter):
    def __init__(self, delay=0, raise_exc=False):
        self.delay = delay
        self.raise_exc = raise_exc

    def classify_transactions(self, transactions):
        if self.raise_exc:
            raise RuntimeError("fail")
        time.sleep(self.delay)
        return ["ok" for _ in transactions]


def test_probe_adapter_success():
    assert probe_adapter(DummyAdapter()) is True


def test_probe_adapter_timeout():
    with pytest.raises(RuntimeError):
        probe_adapter(DummyAdapter(delay=1), timeout=0.01)


def test_probe_adapter_failure():
    with pytest.raises(RuntimeError):
        probe_adapter(DummyAdapter(raise_exc=True))
