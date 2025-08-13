from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import Column, JSON
from sqlmodel import SQLModel, Field


class Upload(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ProcessingJob(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    upload_id: int = Field(foreign_key="upload.id")
    status: str = Field(default="pending")


class UserRule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = None
    label: str
    pattern: str
    match_type: str = "contains"
    field: str = "description"
    priority: int = 0
    confidence: float = 1.0
    version: int = 1
    provenance: str = "user"
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ClassificationResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="processingjob.id")
    result: Optional[str] = None
    status: str = Field(default="queued")


class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="processingjob.id")
    description: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    label: Optional[str] = None
    classification_type: Optional[str] = None


class LLMCost(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="processingjob.id")
    tokens_in: int = 0
    tokens_out: int = 0
    estimated_cost_gbp: float


class ClassifyRequest(SQLModel):
    job_id: int
    user_id: int = 0


class SummaryRequest(SQLModel):
    job_id: int
    user_id: int = 0
