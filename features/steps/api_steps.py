from behave import given, when, then
from httpx import AsyncClient, ASGITransport
import asyncio

from backend.app import app
from sqlmodel import select


@given("an authenticated client")
def given_client(context):
    context.email = "user@example.com"
    transport = ASGITransport(app=app)
    context.client = AsyncClient(transport=transport, base_url="http://test")
    context.loop = asyncio.new_event_loop()
    asyncio.set_event_loop(context.loop)
    async def setup():
        from backend.db import init_db
        init_db()
        resp = await context.client.post("/auth/request", params={"email": context.email})
        assert resp.status_code == 200
        # retrieve token from DB
        from backend.db import get_session
        from backend.models import User
        with get_session() as s:
            user = s.exec(select(User).where(User.email == context.email)).first()
            context.token = user.token
            await context.client.post("/auth/verify", params={"token": context.token})
    context.loop.run_until_complete(setup())


@when('I POST two transactions to "/upload"')
def post_transactions(context):
    txs = [
        {"date": "2024-01-01", "description": "Coffee", "amount": "-1.00"},
        {"date": "2024-01-02", "description": "Bus", "amount": "-2.00"},
    ]
    async def action():
        resp = await context.client.post("/upload", json=txs, params={"token": context.token})
        context.upload_resp = resp
    context.loop.run_until_complete(action())


@then('the summary endpoint reports 2 transactions')
def check_summary(context):
    async def check():
        resp = await context.client.get("/summary", params={"token": context.token})
        assert resp.status_code == 200
        assert resp.json()["transactions"] == 2
    context.loop.run_until_complete(check())
    context.loop.run_until_complete(context.client.aclose())
