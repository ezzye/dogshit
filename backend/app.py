import gzip
import os
from pathlib import Path

from fastapi import FastAPI, Depends, Request, HTTPException, Query
from fastapi.responses import FileResponse
from sqlmodel import Session, select
from .database import init_db, get_session
from .auth import auth_dependency
from .signing import verify_signed_url
from .models import (
    Upload,
    ProcessingJob,
    UserRule,
    ClassificationResult,
    ClassifyRequest,
)
from rules.engine import load_global_rules, merge_rules, evaluate, Rule
from backend.llm_adapter import get_adapter, AbstractAdapter
from bankcleanr.signature import normalise_signature

app = FastAPI()

MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100 MB
ALLOWED_CONTENT_TYPES = {"application/x-ndjson", "text/plain"}


GLOBAL_RULES: list[Rule] = []
SIGNATURE_CACHE: dict[str, dict] = {}


def _convert_user_rule(rule: UserRule) -> Rule:
    return Rule(
        scope="user",
        owner_user_id=str(rule.user_id) if rule.user_id else None,
        active=True,
        priority=rule.priority,
        version=rule.version,
        provenance="user",
        confidence=rule.confidence,
        match={"type": rule.match_type, "pattern": rule.pattern, "fields": [rule.field]},
        action={"label": rule.label, "category": rule.label},
    )


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    global GLOBAL_RULES
    GLOBAL_RULES = load_global_rules()


@app.post("/upload")
async def upload(
    request: Request,
    session: Session = Depends(get_session),
    _: None = Depends(auth_dependency),
) -> dict:
    content_type = request.headers.get("Content-Type", "").split(";")[0].strip()
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported Media Type")
    content_length = int(request.headers.get("Content-Length", 0))
    if content_length > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="Payload too large")

    data = await request.body()
    if len(data) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="Payload too large")
    if request.headers.get("Content-Encoding") == "gzip":
        data = gzip.decompress(data)
    text = data.decode("utf-8")
    upload = Upload(content=text)
    session.add(upload)
    session.commit()
    session.refresh(upload)
    job = ProcessingJob(upload_id=upload.id)
    session.add(job)
    session.commit()
    session.refresh(job)
    return {"job_id": job.id}


@app.get("/status/{job_id}")
def status(
    job_id: int,
    session: Session = Depends(get_session),
    _: None = Depends(auth_dependency),
) -> dict:
    job = session.get(ProcessingJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"status": job.status}


@app.get("/download/{job_id}/{type}")
def download(
    job_id: int,
    type: str,
    request: Request,
    expires: int = Query(...),
    signature: str = Query(...),
    _: None = Depends(auth_dependency),
):
    """Stream a processed file if the signed URL is valid."""

    if type not in {"summary", "report"}:
        raise HTTPException(status_code=400, detail="Invalid type")

    path = request.url.path
    if not verify_signed_url(path, expires, signature):
        raise HTTPException(status_code=403, detail="Invalid or expired URL")

    storage_dir = Path(os.environ.get("STORAGE_DIR", "./storage"))
    file_path = storage_dir / f"{job_id}_{type}.txt"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path)


@app.get("/rules")
def list_rules(
    session: Session = Depends(get_session),
    _: None = Depends(auth_dependency),
):
    rules = session.exec(select(UserRule)).all()
    return rules


@app.post("/rules")
def create_rule(
    rule: UserRule,
    session: Session = Depends(get_session),
    _: None = Depends(auth_dependency),
):
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return rule


@app.post("/classify")
def classify(
    req: ClassifyRequest,
    session: Session = Depends(get_session),
    adapter: AbstractAdapter = Depends(get_adapter),
    _: None = Depends(auth_dependency),
) -> dict:
    job = session.get(ProcessingJob, req.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    upload = session.get(Upload, job.upload_id)
    signature = normalise_signature(upload.content)
    user_rules_all = session.exec(
        select(UserRule).where(UserRule.user_id == req.user_id)
    ).all()
    latest: dict[str, UserRule] = {}
    for r in user_rules_all:
        if r.pattern not in latest or r.version > latest[r.pattern].version:
            latest[r.pattern] = r
    engine_rules = [_convert_user_rule(r) for r in latest.values()]
    rules = merge_rules(GLOBAL_RULES, engine_rules)
    record = {"merchant_signature": signature, "description": upload.content}
    label = evaluate(record, rules)
    if not label:
        if signature not in SIGNATURE_CACHE:
            response = adapter.classify([signature], job_id=req.job_id)[0]
            SIGNATURE_CACHE[signature] = response
        response = SIGNATURE_CACHE[signature]
        label = response["label"]
        confidence = response.get("confidence", 0.0)
        if confidence >= 0.85:
            existing = session.exec(
                select(UserRule)
                .where(UserRule.user_id == req.user_id)
                .where(UserRule.pattern == signature)
                .order_by(UserRule.version.desc())
            ).first()
            if existing:
                if confidence >= 0.95:
                    session.add(
                        UserRule(
                            user_id=req.user_id,
                            label=label,
                            pattern=signature,
                            match_type="exact",
                            field="merchant_signature",
                            priority=existing.priority,
                            confidence=confidence,
                            version=existing.version + 1,
                        )
                    )
                    session.commit()
            else:
                session.add(
                    UserRule(
                        user_id=req.user_id,
                        label=label,
                        pattern=signature,
                        match_type="exact",
                        field="merchant_signature",
                        priority=0,
                        confidence=confidence,
                        version=1,
                    )
                )
                session.commit()
    result = ClassificationResult(job_id=req.job_id, result=label, status="completed")
    session.add(result)
    session.commit()
    session.refresh(result)
    return {"classification_id": result.id, "label": label}
