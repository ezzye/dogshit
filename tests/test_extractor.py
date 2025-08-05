import pytest

from bankcleanr.extractor import extract_transactions
from bankcleanr.parsers import PARSER_REGISTRY


def test_extract_transactions_unknown_bank():
    available = ", ".join(sorted(PARSER_REGISTRY))
    with pytest.raises(ValueError) as excinfo:
        extract_transactions("dummy.pdf", bank="unknown")
    assert str(excinfo.value) == (
        f"Unsupported bank 'unknown'. Available banks: {available}"
    )
