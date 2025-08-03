import gzip
from fastapi import FastAPI, Depends, Request, HTTPException
from sqlmodel import Session, select
from .database import init_db, get_session
from .auth import auth_dependency, generate_token
from .models import (
    Upload,
    ProcessingJob,
    UserRule,
    ClassificationResult,
    ClassifyRequest,
)

app = FastAPI()


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.post("/upload")
async def upload(
    request: Request,
    session: Session = Depends(get_session),
    _: None = Depends(auth_dependency),
) -> dict:
    data = await request.body()
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
def download(job_id: int, type: str, _: None = Depends(auth_dependency)) -> dict:
    if type not in {"summary", "report"}:
        raise HTTPException(status_code=400, detail="Invalid type")
    token = generate_token(f"{job_id}:{type}")
    url = f"https://example.com/download/{job_id}/{type}?token={token}"
    return {"url": url}


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
    result = ClassificationResult(job_id=req.job_id)
    session.add(result)
    session.commit()
    session.refresh(result)
    return {"classification_id": result.id}
