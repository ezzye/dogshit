from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

from bankcleanr.transaction import Transaction
from .base import AbstractAdapter
from bankcleanr.rules import db_store


def load_heuristics_texts() -> tuple[str, str]:
    """Return user and global heuristics as newline separated lines."""
    user, global_ = db_store.get_user_and_global_patterns()
    user_text = "\n".join(f"{label}: {pattern}" for label, pattern in user.items())
    global_text = "\n".join(f"{label}: {pattern}" for label, pattern in global_.items())
    return user_text, global_text


def load_heuristics_text() -> str:
    """Return heuristics as newline separated "label: pattern" lines."""
    patterns = db_store.get_patterns()
    return "\n".join(f"{label}: {pattern}" for label, pattern in patterns.items())


def probe_adapter(adapter: AbstractAdapter, timeout: float = 5.0) -> bool:
    """Send a simple request to verify the adapter is reachable."""
    tx = Transaction(date="1970-01-01", description="probe", amount="0")
    with ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(adapter.classify_transactions, [tx])
        try:
            labels = future.result(timeout=timeout)
        except FutureTimeoutError as exc:  # pragma: no cover - defensive
            raise RuntimeError("timed out") from exc
    if not labels or labels[0] == "unknown":
        raise RuntimeError("no valid response")
    return True
