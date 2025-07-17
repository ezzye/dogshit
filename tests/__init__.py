import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:  # pragma: no cover - this is a test environment check
    import yaml  # type: ignore
except Exception:  # pragma: no cover - only triggered when PyYAML missing
    pytest.skip(
        "PyYAML is required to run the tests. Install it with 'poetry install --with dev'.",
        allow_module_level=True,
    )
