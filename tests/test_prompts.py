import types
from bankcleanr.rules.prompts import CATEGORY_PROMPT


def test_category_prompt_render():
    txn = types.SimpleNamespace(description="Spotify subscription")
    rendered = CATEGORY_PROMPT.render(
        txn=txn,
        user_heuristics="coffee: COFFEE",
        global_heuristics="spotify: SPOTIFY",
    )
    assert "Spotify subscription" in rendered
    assert "coffee: COFFEE" in rendered
    assert "spotify: SPOTIFY" in rendered
    assert "\"category\"" in rendered
    assert "\"new_rule\"" in rendered
