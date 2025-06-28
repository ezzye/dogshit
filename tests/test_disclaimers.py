from bankcleanr.reports.disclaimers import get_disclaimer

def test_disclaimer_contains_keyword():
    text = get_disclaimer()
    assert 'financial advice' in text
