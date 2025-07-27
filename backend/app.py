from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, select
import secrets

from .db import init_db, get_session
from .models import User, UploadedTransaction, Heuristic
from bankcleanr.rules import heuristics as heuristics_mod
from bankcleanr.transaction import Transaction

app = FastAPI()


@app.on_event("startup")
def on_startup() -> None:
    init_db()


def get_current_user(session: Session = Depends(get_session), token: str | None = None) -> User:
    if token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = session.exec(select(User).where(User.token == token)).first()
    if not user or not user.verified:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


@app.post("/auth/request")
def request_magic_link(email: str, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        user = User(email=email)
    user.token = secrets.token_urlsafe(16)
    user.verified = False
    session.add(user)
    session.commit()
    # Instead of sending email, print token
    print(f"Magic link token for {email}: {user.token}")
    return {"detail": "magic link sent"}


@app.post("/auth/verify")
def verify_token(token: str, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.token == token)).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")
    user.verified = True
    session.add(user)
    session.commit()
    return {"detail": "verified"}


@app.post("/upload")
def upload(transactions: list[Transaction], user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    for tx in transactions:
        rec = UploadedTransaction(
            user_id=user.id,
            date=tx.date,
            description=tx.description,
            amount=tx.amount,
        )
        session.add(rec)
    session.commit()
    return {"count": len(transactions)}


@app.get("/heuristics")
def list_heuristics(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    rows = session.exec(select(Heuristic).where(Heuristic.user_id == user.id)).all()
    return rows


@app.post("/heuristics")
def add_heuristic(label: str, pattern: str, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    row = Heuristic(user_id=user.id, label=label, pattern=pattern)
    session.add(row)
    session.commit()
    return row


@app.post("/classify")
def classify(transactions: list[Transaction]):
    labels = heuristics_mod.classify_transactions(transactions)
    return labels


@app.get("/summary")
def summary(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    rows = session.exec(select(UploadedTransaction).where(UploadedTransaction.user_id == user.id)).all()
    return {"transactions": len(rows)}
