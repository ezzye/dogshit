import gzip
from fastapi import FastAPI, Depends, Request, HTTPException, Query
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
from rules.engine import load_global_rules, merge_rules, evaluate

app = FastAPI()

MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100 MB
ALLOWED_CONTENT_TYPES = {"application/x-ndjson", "text/plain"}


GLOBAL_RULES = []


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
) -> dict:
    if type not in {"summary", "report"}:
        raise HTTPException(status_code=400, detail="Invalid type")
    path = request.url.path
    if not verify_signed_url(path, expires, signature):
        raise HTTPException(status_code=403, detail="Invalid or expired URL")
    return {"job_id": job_id, "type": type}


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
    _: None = Depends(auth_dependency),
) -> dict:
    job = session.get(ProcessingJob, req.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    upload = session.get(Upload, job.upload_id)
    user_rules = session.exec(
        select(UserRule).where(UserRule.user_id == req.user_id)
    ).all()
    rules = merge_rules(GLOBAL_RULES, user_rules)
    label = evaluate(upload.content, rules) or "unknown"
    result = ClassificationResult(job_id=req.job_id, result=label, status="completed")
    session.add(result)
    session.commit()
    session.refresh(result)
    return {"classification_id": result.id, "label": label}
