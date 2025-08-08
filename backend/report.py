"""Report generation using LLM and WeasyPrint."""
from __future__ import annotations

import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from typing import Callable, Tuple, Dict

from fastapi import APIRouter, Depends, HTTPException

from .auth import auth_dependency
from .signing import generate_signed_url
from backend.llm_adapter import cost_tracker

from weasyprint import HTML, CSS

# LLM callable returning generated HTML and usage statistics
LLMFunc = Callable[[str], Tuple[str, Dict[str, int]]]

# Accessible A4 stylesheet used by WeasyPrint
A4_CSS = """
@page { size: A4; margin: 2cm; }
body { font-family: Arial, sans-serif; }
"""

router = APIRouter()


def get_llm() -> LLMFunc:
    """Return a callable that sends a prompt to an LLM and returns HTML and usage."""
    import openai

    api_key = os.getenv("OPENAI_API_KEY")
    client = openai.OpenAI(api_key=api_key)
    model = os.getenv("REPORT_MODEL", "gpt-4o-mini")

    def _call(prompt: str) -> Tuple[str, Dict[str, int]]:
        resp = client.chat.completions.create(
            model=model, messages=[{"role": "user", "content": prompt}]
        )
        usage = getattr(resp, "usage", {})
        content = resp.choices[0].message.content or ""
        return content, {
            "prompt_tokens": getattr(usage, "prompt_tokens", 0),
            "completion_tokens": getattr(usage, "completion_tokens", 0),
        }

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

    def _call() -> Tuple[str, Dict[str, int]]:
        return llm(prompt)

    try:
        with ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(_call)
            content, usage = future.result(timeout=30)
    except FutureTimeout as exc:  # pragma: no cover - timeout scenario
        raise RuntimeError("Report generation timed out") from exc

    tokens_in = usage.get("prompt_tokens", usage.get("total_tokens", 0))
    tokens_out = usage.get("completion_tokens", 0)
    tokens = tokens_in + tokens_out
    price_per_1k = float(os.getenv("PRICE_PER_1K_TOKENS_GBP", "0.002"))
    cost = tokens / 1000 * price_per_1k
    cost_tracker.add(job_id, tokens_in, tokens_out, cost)

    html_str = content if isinstance(content, str) else str(content)
    css = CSS(string=A4_CSS)
    pdf_bytes = HTML(string=html_str).write_pdf(stylesheets=[css])

    if len(pdf_bytes) > 5 * 1024 * 1024:
        raise RuntimeError("Generated PDF too large")

    pdf_path = _report_path(job_id)
    pdf_path.write_bytes(pdf_bytes)
    return pdf_path


@router.get("/report/{job_id}")
def get_report(job_id: int, llm: LLMFunc = Depends(get_llm), _: None = Depends(auth_dependency)):
    """Generate a report PDF and return a signed download URL."""
    path = _report_path(job_id)
    if not path.exists():
        try:
            path = generate_report(job_id, llm)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Summary not found")
        except RuntimeError as exc:  # pragma: no cover - error cases
            raise HTTPException(status_code=500, detail=str(exc))

    url = generate_signed_url(f"/download/{job_id}/report")
    return {"url": url}


__all__ = ["router", "get_llm", "generate_report"]
