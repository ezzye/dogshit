from __future__ import annotations

from tenacity import retry as tenacity_retry, stop_after_attempt, wait_exponential


def retry(*, attempts: int = 3, multiplier: float = 1, min_wait: float = 1, max_wait: float = 4):
    """Return a tenacity retry decorator with exponential backoff."""
    return tenacity_retry(
        wait=wait_exponential(multiplier=multiplier, min=min_wait, max=max_wait),
        stop=stop_after_attempt(attempts),
    )
