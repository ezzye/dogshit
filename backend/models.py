from typing import Optional
from pydantic import BaseModel
from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str
    token: Optional[str] = None
    verified: bool = False


class UploadedTransaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    date: str
    description: str
    amount: str


class Heuristic(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    label: str
    pattern: str


class NewHeuristic(BaseModel):
    label: str
    pattern: str
