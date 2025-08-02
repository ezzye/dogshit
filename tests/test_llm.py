from bankcleanr.llm import classify_transactions, PROVIDERS
import bankcleanr.llm as llm_mod
from bankcleanr.transaction import Transaction
from bankcleanr.llm.openai import OpenAIAdapter
from bankcleanr.llm.mistral import MistralAdapter
from bankcleanr.llm.gemini import GeminiAdapter
from bankcleanr.llm.bfl import BFLAdapter
from bankcleanr.settings import Settings
from pathlib import Path
import importlib
import pytest
from sqlmodel import create_engine


@pytest.fixture(autouse=True)
def _db(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    db_file = tmp_path / "rules.db"
    from bankcleanr.rules import db_store, regex, heuristics as heuristics_mod

    importlib.reload(db_store)
    db_store.DB_PATH = db_file
    db_store.engine = create_engine(f"sqlite:///{db_file}", echo=False)
    db_store.init_db()
    importlib.reload(regex)
    regex.reload_patterns()
    importlib.reload(heuristics_mod)
    yield

class DummyAdapter(OpenAIAdapter):
    def __init__(self, label="remote", **kwargs):
        self.label = label

    def classify_transactions(self, transactions):
        return [{"category": self.label, "new_rule": None} for _ in transactions]


def test_llm_fallback(monkeypatch):
    monkeypatch.setitem(PROVIDERS, "openai", DummyAdapter)
    txs = [
        Transaction(date="2024-01-01", description="Spotify premium", amount="-9.99"),
        Transaction(date="2024-01-02", description="Coffee shop", amount="-2.00"),
    ]
    labels = classify_transactions(txs, provider="openai")
    assert labels == ["spotify", "remote"]


def test_get_adapter_passes_api_key(monkeypatch):
    captured = {}

    class CaptureAdapter(OpenAIAdapter):
        def __init__(self, *args, **kwargs):
            captured["api_key"] = kwargs.get("api_key")

    monkeypatch.setitem(PROVIDERS, "openai", CaptureAdapter)
    settings = Settings(llm_provider="openai", api_key="secret", config_path=Path("cfg"))
    monkeypatch.setattr("bankcleanr.llm.get_settings", lambda: settings)
    from bankcleanr.llm import get_adapter

    get_adapter()
    assert captured["api_key"] == "secret"


def test_llm_masks_before_sending(monkeypatch):
    captured = {}

    class CaptureAdapter(OpenAIAdapter):
        def __init__(self, *args, **kwargs):
            pass

        def classify_transactions(self, transactions):
            captured["descriptions"] = [tx.description for tx in transactions]
            return [{"category": "remote", "new_rule": None} for _ in transactions]

    monkeypatch.setitem(PROVIDERS, "openai", CaptureAdapter)
    txs = [Transaction(date="2024-01-01", description="Send 12-34-56 12345678", amount="-9.99")]
    classify_transactions(txs, provider="openai")
    assert captured["descriptions"][0] == "Send ****3456 ****5678"


def test_mistral_fallback(monkeypatch):
    monkeypatch.setitem(PROVIDERS, "mistral", DummyAdapter)
    txs = [
        Transaction(date="2024-01-01", description="Spotify premium", amount="-9.99"),
        Transaction(date="2024-01-02", description="Coffee shop", amount="-2.00"),
    ]
    labels = classify_transactions(txs, provider="mistral")
    assert labels == ["spotify", "remote"]


def test_gemini_fallback(monkeypatch):
    monkeypatch.setitem(PROVIDERS, "gemini", DummyAdapter)
    txs = [
        Transaction(date="2024-01-01", description="Spotify premium", amount="-9.99"),
        Transaction(date="2024-01-02", description="Coffee shop", amount="-2.00"),
    ]
    labels = classify_transactions(txs, provider="gemini")
    assert labels == ["spotify", "remote"]


def test_bfl_fallback(monkeypatch):
    monkeypatch.setitem(PROVIDERS, "bfl", DummyAdapter)
    txs = [
        Transaction(date="2024-01-01", description="Spotify premium", amount="-9.99"),
        Transaction(date="2024-01-02", description="Coffee shop", amount="-2.00"),
    ]
    labels = classify_transactions(txs, provider="bfl")
    assert labels == ["spotify", "remote"]


def test_get_bfl_adapter_passes_api_key(monkeypatch):
    captured = {}

    class CaptureAdapter(BFLAdapter):
        def __init__(self, *args, **kwargs):
            captured["api_key"] = kwargs.get("api_key")

    monkeypatch.setitem(PROVIDERS, "bfl", CaptureAdapter)
    settings = Settings(llm_provider="bfl", api_key="secret", config_path=Path("cfg"))
    monkeypatch.setattr("bankcleanr.llm.get_settings", lambda: settings)
    from bankcleanr.llm import get_adapter

    get_adapter()
    assert captured["api_key"] == "secret"


def test_get_mistral_adapter_passes_api_key(monkeypatch):
    captured = {}

    class CaptureAdapter(MistralAdapter):
        def __init__(self, *args, **kwargs):
            captured["api_key"] = kwargs.get("api_key")

    monkeypatch.setitem(PROVIDERS, "mistral", CaptureAdapter)
    settings = Settings(llm_provider="mistral", api_key="secret", config_path=Path("cfg"))
    monkeypatch.setattr("bankcleanr.llm.get_settings", lambda: settings)
    from bankcleanr.llm import get_adapter

    get_adapter()
    assert captured["api_key"] == "secret"


def test_get_gemini_adapter_passes_api_key(monkeypatch):
    captured = {}

    class CaptureAdapter(GeminiAdapter):
        def __init__(self, *args, **kwargs):
            captured["api_key"] = kwargs.get("api_key")

    monkeypatch.setitem(PROVIDERS, "gemini", CaptureAdapter)
    settings = Settings(llm_provider="gemini", api_key="secret", config_path=Path("cfg"))
    monkeypatch.setattr("bankcleanr.llm.get_settings", lambda: settings)
    from bankcleanr.llm import get_adapter

    get_adapter()
    assert captured["api_key"] == "secret"


def test_get_bfl_adapter_uses_env(monkeypatch, tmp_path):
    """BFL adapter should read API key from BFL_API_KEY."""
    cfg = tmp_path / "config.yml"
    cfg.write_text("llm_provider: bfl")
    monkeypatch.setenv("BFL_API_KEY", "bfl-env")
    monkeypatch.setenv("OPENAI_API_KEY", "should-not-be-used")

    from bankcleanr.settings import load_settings
    monkeypatch.setattr("bankcleanr.llm.get_settings", lambda: load_settings(cfg))

    captured = {}

    class CaptureAdapter(BFLAdapter):
        def __init__(self, *args, **kwargs):
            captured["api_key"] = kwargs.get("api_key")

    monkeypatch.setitem(PROVIDERS, "bfl", CaptureAdapter)
    from bankcleanr.llm import get_adapter

    get_adapter()
    assert captured["api_key"] == "bfl-env"


def test_get_bfl_adapter_falls_back_to_openai(monkeypatch, tmp_path):
    """If BFL_API_KEY is not set, fall back to OPENAI_API_KEY."""
    cfg = tmp_path / "config.yml"
    cfg.write_text("llm_provider: bfl")
    monkeypatch.delenv("BFL_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "openai-env")

    from bankcleanr.settings import load_settings
    monkeypatch.setattr("bankcleanr.llm.get_settings", lambda: load_settings(cfg))

    captured = {}

    class CaptureAdapter(BFLAdapter):
        def __init__(self, *args, **kwargs):
            captured["api_key"] = kwargs.get("api_key")

    monkeypatch.setitem(PROVIDERS, "bfl", CaptureAdapter)
    from bankcleanr.llm import get_adapter

    get_adapter()
    assert captured["api_key"] == "openai-env"


def test_llm_adds_patterns_and_reuses(monkeypatch, tmp_path):
    monkeypatch.setenv("APP_ENV", "test")
    db_file = tmp_path / "rules.db"
    import importlib
    from sqlmodel import create_engine
    from bankcleanr.rules import db_store, regex

    importlib.reload(db_store)
    db_store.DB_PATH = db_file
    db_store.engine = create_engine(f"sqlite:///{db_file}", echo=False)
    db_store.init_db()
    importlib.reload(regex)
    regex.reload_patterns()

    calls = {"n": 0}

    class DummyAdapter(OpenAIAdapter):
        def __init__(self, *a, **k):
            pass

        def classify_transactions(self, txs):
            calls["n"] += 1
            return [{"category": "coffee", "new_rule": None} for _ in txs]

    monkeypatch.setitem(PROVIDERS, "openai", DummyAdapter)

    txs = [Transaction(date="2024-01-01", description="Coffee shop", amount="-1")]
    labels = classify_transactions(txs, provider="openai")
    assert labels == ["coffee"]
    assert db_store.get_patterns()["coffee"] == "Coffee shop"

    labels = classify_transactions(txs, provider="openai")
    assert labels == ["coffee"]
    assert calls["n"] == 1


def test_reclassification_after_learning(monkeypatch):
    from bankcleanr.rules import manager as manager_mod

    call_count = {"n": 0}

    original = manager_mod.Manager.classify

    def spy(self, txs):
        call_count["n"] += 1
        return original(self, txs)

    monkeypatch.setattr(manager_mod.Manager, "classify", spy)

    class CaptureAdapter(OpenAIAdapter):
        def __init__(self, *a, **k):
            self.last_details = [{"category": "coffee", "new_rule": None}]

        def classify_transactions(self, txs):
            return self.last_details

    adapter = CaptureAdapter()
    monkeypatch.setattr(llm_mod, "get_adapter", lambda *a, **k: adapter)

    txs = [Transaction(date="2024-01-01", description="Coffee shop", amount="-1")]
    labels = llm_mod.classify_transactions(txs, provider="openai")

    assert labels == ["coffee"]
    assert call_count["n"] == 2
    assert adapter.last_details == [{"category": "coffee", "new_rule": None}]


