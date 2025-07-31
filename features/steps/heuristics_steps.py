from behave import given, when, then

from pathlib import Path
import importlib
import os
import tempfile
import urllib.parse
import urllib.request

import yaml
from sqlmodel import create_engine

from bankcleanr.transaction import Transaction
from bankcleanr.rules import regex
from bankcleanr.rules import heuristics, db_store


@given("sample transactions")
def given_transactions(context):
    context.txs = [
        Transaction(date="2024-01-01", description="Spotify premium", amount="-9.99"),
        Transaction(date="2024-01-02", description="Amazon Prime membership", amount="-8.99"),
        Transaction(date="2024-01-03", description="Dropbox yearly", amount="-119.00"),
        Transaction(date="2024-01-04", description="Coffee", amount="-2.00"),
    ]


@when("I classify transactions locally")
def classify(context):
    context.labels = heuristics.classify_transactions(context.txs)


@then("the labels are")
def check_labels(context):
    expected = [row[0] for row in context.table.rows]
    assert context.labels == expected


@given("a heuristics database containing")
def heuristics_db(context):
    data = {row["label"]: row["pattern"] for row in context.table}
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.close()
    context.db_file = Path(tmp.name)
    context._orig_app_env = os.getenv("APP_ENV")
    os.environ["APP_ENV"] = "test"
    importlib.reload(db_store)
    db_store.DB_PATH = context.db_file
    db_store.engine = create_engine(f"sqlite:///{context.db_file}", echo=False)
    db_store.init_db()
    for label, pattern in data.items():
        db_store.add_pattern(label, pattern)
    regex.reload_patterns()
    importlib.reload(heuristics)


@given('a transaction "{description}"')
def single_transaction(context, description):
    context.txs = [Transaction(date="2024-01-01", description=description, amount="-1.00")]


@given("backend environment variables")
def backend_env(context):
    context._orig_backend_url = os.getenv("BANKCLEANR_BACKEND_URL")
    context._orig_backend_token = os.getenv("BANKCLEANR_BACKEND_TOKEN")
    os.environ["BANKCLEANR_BACKEND_URL"] = "http://test"
    os.environ["BANKCLEANR_BACKEND_TOKEN"] = context.token
    context._orig_urlopen = urllib.request.urlopen

    def _fake_urlopen(req, timeout=5):
        url = urllib.parse.urlparse(req.full_url)
        path = url.path
        if url.query:
            path += "?" + url.query

        async def _call():
            resp = await context.client.post(path, content=req.data, headers=req.headers)
            class R:
                def read(self_inner):
                    return resp.content

            return R()

        return context.loop.run_until_complete(_call())

    urllib.request.urlopen = _fake_urlopen


@when('I learn a pattern labeled "{label}" for "{description}"')
def learn_pattern(context, label, description):
    txs = [Transaction(date="2024-01-01", description=description, amount="-1.00")]
    heuristics.learn_new_patterns(txs, [label], confirm=lambda _: "y")


@then('the backend has a heuristic labeled "{label}"')
def backend_has_rule(context, label):
    async def check():
        resp = await context.client.get("/heuristics", params={"token": context.token})
        assert resp.status_code == 200
        assert any(r["label"] == label for r in resp.json())

    context.loop.run_until_complete(check())


