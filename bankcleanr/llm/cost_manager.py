import json
import os
from pathlib import Path
from datetime import date
from typing import Callable

class DailyCostManager:
    """Track and persist daily LLM spend."""

    def __init__(
        self,
        max_cost: float | None = None,
        path: Path | None = None,
        today_fn: Callable[[], date] | None = None,
    ) -> None:
        self.max_cost = (
            max_cost
            if max_cost is not None
            else float(os.getenv("MAX_LLM_COST_PER_DAY", "inf"))
        )
        default_path = Path(os.getenv("LLM_COST_PATH", Path.home() / ".bankcleanr_llm_cost.json"))
        self.path = path or default_path
        self.today_fn = today_fn or date.today
        self._data = {"date": self.today_fn().isoformat(), "spend": 0.0}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text())
            except Exception:
                data = {}
            today = self.today_fn().isoformat()
            if data.get("date") == today:
                self._data = {"date": today, "spend": float(data.get("spend", 0.0))}
            else:
                self._data = {"date": today, "spend": 0.0}
        else:
            self._save()

    def _save(self) -> None:
        self.path.write_text(json.dumps(self._data))

    def _ensure_today(self) -> None:
        today = self.today_fn().isoformat()
        if self._data.get("date") != today:
            self._data = {"date": today, "spend": 0.0}
            self._save()

    @property
    def spend(self) -> float:
        self._ensure_today()
        return float(self._data.get("spend", 0.0))

    def check_and_add(self, cost: float) -> None:
        """Raise if adding cost would exceed max; otherwise persist."""
        self._ensure_today()
        new_spend = self._data["spend"] + cost
        if new_spend > self.max_cost:
            raise RuntimeError("daily llm cost limit exceeded")
        self._data["spend"] = new_spend
        self._save()


def estimate_tokens(text: str) -> int:
    """Rough token estimation using 4 chars per token."""
    return max(1, len(text) // 4)


cost_manager = DailyCostManager()
