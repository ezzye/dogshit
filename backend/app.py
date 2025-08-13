import gzip
import os
from pathlib import Path

from fastapi import FastAPI, Depends, Request, HTTPException, Query, UploadFile, File
from fastapi.responses import FileResponse
from .report import router as report_router
from sqlmodel import Session, select
from .database import init_db, get_session
from .auth import auth_dependency
from .signing import verify_signed_url
from .models import (
    Upload,
    ProcessingJob,
    UserRule,
    ClassifyRequest,
    LLMCost,
    Transaction,
)
from rules.engine import (
    load_global_rules,
    merge_rules,
    evaluate,
    Rule,
    norm,
    Match,
    Action,
    CATEGORIES,
)
from backend.llm_adapter import get_adapter, AbstractAdapter
from bankcleanr.signature import normalise_signature
import json
from datetime import datetime

app = FastAPI()

MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100 MB
ALLOWED_CONTENT_TYPES = {
    "application/x-ndjson",
    "text/plain",
    "application/octet-stream",
    "",
}


GLOBAL_RULES: list[Rule] = []
SIGNATURE_CACHE: dict[str, dict] = {}

app.include_router(report_router)

def _convert_user_rule(rule: UserRule) -> Rule:
    return Rule(
        scope="user",
        owner_user_id=str(rule.user_id) if rule.user_id else None,
        active=True,
        priority=rule.priority,
        version=rule.version,
        provenance=rule.provenance,
        confidence=rule.confidence,
        match=Match(type=rule.match_type, pattern=rule.pattern, fields=[rule.field]),
        action=Action(label=rule.label, category=rule.label),
    )


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    global GLOBAL_RULES
    GLOBAL_RULES = load_global_rules()


@app.post("/upload")
async def upload(
    request: Request,
    file: UploadFile | None = File(None),
    session: Session = Depends(get_session),
    _: None = Depends(auth_dependency),
) -> dict:
    base_content_type = request.headers.get("Content-Type", "").split(";")[0].strip()
    content_length = int(request.headers.get("Content-Length", 0))
    if content_length > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="Payload too large")

    if base_content_type.startswith("multipart/form-data"):
        if file is None:
            raise HTTPException(status_code=400, detail="No file provided")
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(status_code=415, detail="Unsupported Media Type")
        data = await file.read()
    else:
        if base_content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(status_code=415, detail="Unsupported Media Type")
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
    job = ProcessingJob(upload_id=upload.id, status="uploaded")
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


@app.get("/costs/{job_id}")
def costs(
    job_id: int,
    session: Session = Depends(get_session),
    _: None = Depends(auth_dependency),
) -> dict:
    job = session.get(ProcessingJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    entries = session.exec(select(LLMCost).where(LLMCost.job_id == job_id)).all()
    tokens_in = sum(e.tokens_in for e in entries)
    tokens_out = sum(e.tokens_out for e in entries)
    total_tokens = tokens_in + tokens_out
    estimated_cost_gbp = sum(e.estimated_cost_gbp for e in entries)
    return {
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "total_tokens": total_tokens,
        "estimated_cost_gbp": estimated_cost_gbp,
    }


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
    ext = "pdf" if type == "report" else "txt"
    file_path = storage_dir / f"{job_id}_{type}.{ext}"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    media_type = "application/pdf" if type == "report" else "text/plain"
    return FileResponse(file_path, media_type=media_type)


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
    normalised = norm(rule.pattern)
    if sum(c.isalpha() for c in normalised) < 6:
        raise HTTPException(
            status_code=400,
            detail="Pattern must contain at least 6 alphabetic characters",
        )
    # store the normalised pattern so duplicates are matched consistently
    rule.pattern = normalised
    if rule.label not in CATEGORIES:
        raise HTTPException(status_code=400, detail="Unknown category label")
    existing = session.exec(
        select(UserRule)
        .where(UserRule.user_id == rule.user_id)
        .where(UserRule.pattern == rule.pattern)
        .order_by(UserRule.version.desc())  # type: ignore[attr-defined]
    ).first()
    if existing:
        if existing.field != rule.field:
            raise HTTPException(
                status_code=400, detail="Field coverage cannot be narrower"
            )
        if rule.confidence <= existing.confidence:
            return existing
        rule.version = existing.version + 1
        rule.priority = existing.priority
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
    if upload is None:
        raise HTTPException(status_code=404, detail="Upload not found")
    # Update status so async clients know work has started
    job.status = "processing"
    session.add(job)
    session.commit()
    try:
        # Parse NDJSON content into transaction records
        transactions = []
        for line in upload.content.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                tx = json.loads(line)
            except json.JSONDecodeError as e:
                raise HTTPException(status_code=400, detail=f"Invalid JSON line: {e}")
            description = tx.get("description", "")
            signature = normalise_signature(description)
            tx_record = {**tx, "merchant_signature": signature}
            transactions.append(tx_record)

        user_rules_all = session.exec(
            select(UserRule).where(UserRule.user_id == req.user_id)
        ).all()
        latest: dict[str, UserRule] = {}
        for r in user_rules_all:
            if r.pattern not in latest or r.version > latest[r.pattern].version:
                latest[r.pattern] = r
        engine_rules = [_convert_user_rule(r) for r in latest.values()]
        rules = merge_rules(GLOBAL_RULES, engine_rules)

        unknown_signatures = []
        for tx in transactions:
            label = evaluate(tx, rules)
            tx["_label"] = label
            if not label:
                sig = tx["merchant_signature"]
                if sig not in SIGNATURE_CACHE and sig not in unknown_signatures:
                    unknown_signatures.append(sig)

        if unknown_signatures:
            responses = adapter.classify(unknown_signatures, job_id=req.job_id)
            for sig, resp in zip(unknown_signatures, responses):
                SIGNATURE_CACHE[sig] = resp

        processed_signatures: set[str] = set()
        enriched: list[dict] = []
        for tx in transactions:
            label = tx.get("_label")
            source = "rule" if label else "llm"
            sig = tx["merchant_signature"]
            if not label:
                response = SIGNATURE_CACHE[sig]
                label = response["label"]
                confidence = response.get("confidence", 0.0)
                if sig not in processed_signatures and confidence >= 0.85:
                    if sum(c.isalpha() for c in norm(sig)) < 6:
                        processed_signatures.add(sig)
                    else:
                        existing = session.exec(
                            select(UserRule)
                            .where(UserRule.user_id == req.user_id)
                            .where(UserRule.pattern == sig)
                            .order_by(UserRule.version.desc())  # type: ignore[attr-defined]
                        ).first()
                        if existing:
                            if (
                                existing.field != "merchant_signature"
                                or confidence < 0.95
                                or confidence <= existing.confidence
                            ):
                                processed_signatures.add(sig)
                            else:
                                existing.label = label
                                existing.confidence = confidence
                                existing.version = existing.version + 1
                                existing.provenance = "llm"
                                existing.updated_at = datetime.utcnow()
                                session.add(existing)
                                session.commit()
                        else:
                            session.add(
                                UserRule(
                                    user_id=req.user_id,
                                    label=label,
                                    pattern=sig,
                                    match_type="exact",
                                    field="merchant_signature",
                                    priority=0,
                                    confidence=confidence,
                                    version=1,
                                    provenance="llm",
                                )
                            )
                            session.commit()
                processed_signatures.add(sig)
            if not label:
                label = "unknown"
                source = "unknown"
            tx["label"] = label
            tx["type"] = source
            transaction = Transaction(
                job_id=req.job_id,
                description=tx.get("description"),
                data=tx,
                label=label,
                classification_type=source,
            )
            session.add(transaction)
            session.commit()
            enriched.append(tx)

        # Mark completion
        job.status = "completed"
        session.add(job)
        session.commit()
        return {"transactions": enriched}
    except Exception:
        job.status = "failed"
        session.add(job)
        session.commit()
        raise


@app.get("/transactions/{job_id}")
def list_transactions(
    job_id: int,
    type: str | None = Query(None),
    description: str | None = Query(None),
    session: Session = Depends(get_session),
    _: None = Depends(auth_dependency),
):
    query = select(Transaction).where(Transaction.job_id == job_id)
    if type:
        query = query.where(Transaction.classification_type == type)
    if description:
        query = query.where(Transaction.description.contains(description))
    entries = session.exec(query).all()
    return [t.data for t in entries]
