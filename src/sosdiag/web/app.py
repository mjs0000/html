from __future__ import annotations

import json
import os
import re
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape
from starlette.concurrency import run_in_threadpool

from sosdiag.batch import analyze_corpus
from sosdiag.model.report import (
    CustomerContact,
    CustomerInfo,
    ExecutionInfo,
    ExecutionPeriod,
    Person,
    ReportInfo,
    ReportMetadata,
)
from sosdiag.renderer.html import render_html
from sosdiag.reporting import build_report, corpus_run_summary

APP_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = Path(os.environ.get("SOSDIAG_DATA_DIR", "/app/data"))
UPLOAD_DIR = DATA_DIR / "uploads"
OUTPUT_DIR = DATA_DIR / "output"
WEB_TEMPLATE_DIR = APP_ROOT / "templates" / "web"
_UPLOAD_CHUNK_SIZE = 1024 * 1024

for directory in (UPLOAD_DIR, OUTPUT_DIR):
    directory.mkdir(parents=True, exist_ok=True)

env = Environment(
    loader=FileSystemLoader(WEB_TEMPLATE_DIR),
    autoescape=select_autoescape(["html", "xml"]),
)

app = FastAPI(title="sosreport Structure Diagnostic")


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    template = env.get_template("index.html.j2")
    return HTMLResponse(template.render())


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/reports", response_class=HTMLResponse)
async def create_report(
    sosreports: Annotated[list[UploadFile], File(...)],
    customer_name: Annotated[str, Form(...)],
    execution_period: Annotated[str, Form(...)],
    location: Annotated[str, Form(...)],
    customer_contact: Annotated[str, Form("")],
    sales_name: Annotated[str, Form("")],
    sales_role: Annotated[str, Form("")],
    sales_phone: Annotated[str, Form("")],
    sales_email: Annotated[str, Form("")],
    engineer_name: Annotated[str, Form("")],
    engineer_role: Annotated[str, Form("")],
    engineer_phone: Annotated[str, Form("")],
    engineer_email: Annotated[str, Form("")],
) -> HTMLResponse:
    if not sosreports:
        raise HTTPException(status_code=400, detail="sosreport 파일이 필요합니다.")

    job_id = uuid.uuid4().hex[:12]
    job_date = datetime.now().strftime("%Y%m%d")
    customer_key = _safe_customer_key(customer_name)
    job_key = f"{customer_key}_{job_date}_{job_id}"

    job_upload_dir = UPLOAD_DIR / job_key
    job_output_dir = OUTPUT_DIR / job_key
    job_upload_dir.mkdir(parents=True, exist_ok=False)
    job_output_dir.mkdir(parents=True, exist_ok=False)

    saved_paths: list[Path] = []
    saved_names: set[str] = set()
    try:
        for upload in sosreports:
            safe_name = Path(upload.filename or "").name
            _validate_sosreport_filename(safe_name)
            if safe_name in saved_names:
                raise HTTPException(status_code=400, detail=f"중복 파일명: {safe_name}")

            target = job_upload_dir / safe_name
            with target.open("wb") as fh:
                while True:
                    chunk = await upload.read(_UPLOAD_CHUNK_SIZE)
                    if not chunk:
                        break
                    fh.write(chunk)
            await upload.close()

            if target.stat().st_size == 0:
                raise HTTPException(status_code=400, detail=f"빈 파일은 분석할 수 없습니다: {safe_name}")

            saved_names.add(safe_name)
            saved_paths.append(target)

        metadata = _build_report_metadata(
            customer_name=customer_name,
            execution_period=execution_period,
            location=location,
            customer_contact=customer_contact,
            sales_name=sales_name,
            sales_role=sales_role,
            sales_phone=sales_phone,
            sales_email=sales_email,
            engineer_name=engineer_name,
            engineer_role=engineer_role,
            engineer_phone=engineer_phone,
            engineer_email=engineer_email,
        )

        # Analyze every uploaded archive exactly once. The batch result retains the
        # full per-host payloads so JSON and HTML are produced from the same run.
        corpus = await run_in_threadpool(analyze_corpus, saved_paths)

        json_path = job_output_dir / "corpus-analysis.json"
        json_path.write_text(
            json.dumps(corpus, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        report = build_report(
            corpus.get("payloads", []),
            metadata,
            run_summary=corpus_run_summary(corpus),
        )
        html_path = job_output_dir / "report.html"
        await run_in_threadpool(render_html, report, html_path)

        generated = [
            {
                "name": "report.html",
                "url": f"/reports/{job_key}/report.html",
                "label": "통합 HTML 보고서",
            },
            {
                "name": "corpus-analysis.json",
                "url": f"/reports/{job_key}/corpus-analysis.json",
                "label": "분석 JSON",
            },
        ]

        template = env.get_template("result.html.j2")
        return HTMLResponse(
            template.render(
                job_id=job_id,
                job_key=job_key,
                customer_name=customer_name,
                uploaded=[path.name for path in saved_paths],
                generated=generated,
                analyzed_count=corpus.get("analyzed_count", 0),
                error_count=corpus.get("error_count", 0),
            )
        )
    except HTTPException:
        shutil.rmtree(job_upload_dir, ignore_errors=True)
        shutil.rmtree(job_output_dir, ignore_errors=True)
        raise
    except Exception as exc:
        shutil.rmtree(job_upload_dir, ignore_errors=True)
        shutil.rmtree(job_output_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"보고서 생성 실패: {type(exc).__name__}: {exc}") from exc


@app.get("/reports/{job_key}/{filename}")
def download_report(job_key: str, filename: str) -> FileResponse:
    if Path(job_key).name != job_key or Path(filename).name != filename:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")

    target = OUTPUT_DIR / job_key / filename
    if not target.is_file():
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
    return FileResponse(target, filename=filename)


def _validate_sosreport_filename(filename: str) -> None:
    if not filename or filename != Path(filename).name:
        raise HTTPException(status_code=400, detail="올바르지 않은 파일명입니다.")
    if not filename.startswith("sosreport-") or ".tar" not in filename:
        raise HTTPException(
            status_code=400,
            detail=f"sosreport archive 형식이 아닙니다: {filename}",
        )


def _safe_customer_key(customer_name: str) -> str:
    value = customer_name.strip().replace(" ", "_")
    value = re.sub(r"[^\w.-]+", "_", value, flags=re.UNICODE)
    value = re.sub(r"_+", "_", value).strip("_.")
    return value or "customer"


def _build_report_metadata(
    *,
    customer_name: str,
    execution_period: str,
    location: str,
    customer_contact: str,
    sales_name: str,
    sales_role: str,
    sales_phone: str,
    sales_email: str,
    engineer_name: str,
    engineer_role: str,
    engineer_phone: str,
    engineer_email: str,
) -> ReportMetadata:
    start, end = _parse_execution_period(execution_period)
    contact = CustomerContact(name=customer_contact.strip()) if customer_contact.strip() else None
    sales = (
        Person(
            name=sales_name.strip(),
            role=sales_role.strip() or None,
            phone=sales_phone.strip() or None,
            email=sales_email.strip() or None,
        )
        if sales_name.strip()
        else None
    )
    engineers = []
    if engineer_name.strip():
        engineers.append(
            Person(
                name=engineer_name.strip(),
                role=engineer_role.strip() or None,
                phone=engineer_phone.strip() or None,
                email=engineer_email.strip() or None,
            )
        )

    return ReportMetadata(
        report=ReportInfo(
            title=f"{customer_name.strip()} RHEL Health Check Report",
            report_date=datetime.now().strftime("%Y-%m-%d"),
        ),
        customer=CustomerInfo(
            name=customer_name.strip(),
            site=location.strip() or None,
            contact=contact,
        ),
        execution=ExecutionInfo(
            period=ExecutionPeriod(start=start, end=end),
            location=location.strip() or None,
        ),
        sales_representative=sales,
        technical_engineers=engineers,
    )


def _parse_execution_period(value: str) -> tuple[str | None, str | None]:
    text = value.strip()
    if not text:
        return None, None
    for separator in ("~", "–", "—", " to "):
        if separator in text:
            start, end = text.split(separator, 1)
            return start.strip() or None, end.strip() or None
    return text, None


def main() -> None:
    import uvicorn

    uvicorn.run("sosdiag.web.app:app", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
