"""Report generation using LLM and WeasyPrint."""
from __future__ import annotations

import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from typing import Callable, Union

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from .auth import auth_dependency

# Type alias for LLM callable which takes prompt string and returns
# either HTML string or PDF bytes
LLMFunc = Callable[[str], Union[str, bytes]]

router = APIRouter()


def get_llm() -> LLMFunc:
    """Return a callable that sends a prompt to an LLM."""
    import openai

    api_key = os.getenv("OPENAI_API_KEY")
    client = openai.OpenAI(api_key=api_key)
    model = os.getenv("REPORT_MODEL", "gpt-4o-mini")

    def _call(prompt: str) -> str:
        resp = client.chat.completions.create(
            model=model, messages=[{"role": "user", "content": prompt}]
        )
        return resp.choices[0].message.content or ""

    return _call


def _summary_path(job_id: int) -> Path:
    storage_dir = Path(os.environ.get("STORAGE_DIR", "./storage"))
    return storage_dir / f"{job_id}_summary_v1.json"


def _report_path(job_id: int) -> Path:
    storage_dir = Path(os.environ.get("STORAGE_DIR", "./storage"))
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir / f"{job_id}_report.pdf"


def generate_report(job_id: int, llm: LLMFunc) -> Path:
    """Generate a PDF report for the given job using the provided LLM."""
    summary_file = _summary_path(job_id)
    if not summary_file.exists():
        raise FileNotFoundError("Summary not found")
    prompt = summary_file.read_text(encoding="utf-8")

    def _call() -> Union[str, bytes]:
        return llm(prompt)

    try:
        with ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(_call)
            content = future.result(timeout=30)
    except FutureTimeout as exc:  # pragma: no cover - timeout scenario
        raise RuntimeError("Report generation timed out") from exc

    if isinstance(content, bytes) and content.startswith(b"%PDF"):
        pdf_bytes = content
    else:
        from weasyprint import HTML

        html_str = content.decode("utf-8") if isinstance(content, bytes) else str(content)
        pdf_bytes = HTML(string=html_str).write_pdf()

    if len(pdf_bytes) > 5 * 1024 * 1024:
        raise RuntimeError("Generated PDF too large")

    pdf_path = _report_path(job_id)
    pdf_path.write_bytes(pdf_bytes)
    return pdf_path


@router.get("/report/{job_id}")
def get_report(job_id: int, llm: LLMFunc = Depends(get_llm), _: None = Depends(auth_dependency)):
    """Return the report PDF for the given job ID, generating it if necessary."""
    path = _report_path(job_id)
    if not path.exists():
        try:
            path = generate_report(job_id, llm)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Summary not found")
        except RuntimeError as exc:  # pragma: no cover - error cases
            raise HTTPException(status_code=500, detail=str(exc))
    return FileResponse(path, media_type="application/pdf")


__all__ = ["router", "get_llm", "generate_report"]
