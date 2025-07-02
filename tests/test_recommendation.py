import yaml
from bankcleanr.transaction import Transaction
from bankcleanr.recommendation import load_knowledge_base, recommend_transactions


def test_load_knowledge_base(tmp_path):
    data = {"foo": {"url": "x"}}
    path = tmp_path / "kb.yml"
    path.write_text(yaml.safe_dump(data))
    result = load_knowledge_base(path)
    assert result == data


def test_recommend_transactions(monkeypatch, tmp_path):
    kb = {"spotify": {"url": "cancel"}}
    kb_file = tmp_path / "kb.yml"
    kb_file.write_text(yaml.safe_dump(kb))

    txs = [Transaction(date="2024-01-01", description="Spotify", amount="-9.99")]

    def dummy_classify(transactions, provider=None):
        return ["spotify"]

    monkeypatch.setattr("bankcleanr.recommendation.classify_transactions", dummy_classify)
    recs = recommend_transactions(txs, kb_path=kb_file)
    assert recs[0].category == "spotify"
    assert recs[0].action == "Cancel"
    assert recs[0].info["url"] == "cancel"
