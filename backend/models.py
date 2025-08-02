from datetime import datetime
from typing import Optional
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
    rule_text: str


class ClassificationResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="processingjob.id")
    result: Optional[str] = None
    status: str = Field(default="queued")


class ClassifyRequest(SQLModel):
    job_id: int
