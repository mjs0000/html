from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape

APP_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = Path("/app/data")
UPLOAD_DIR = DATA_DIR / "uploads"
OUTPUT_DIR = DATA_DIR / "output"
WEB_TEMPLATE_DIR = APP_ROOT / "templates" / "web"

for directory in (UPLOAD_DIR, OUTPUT_DIR):
    directory.mkdir(parents=True, exist_ok=True)

env = Environment(
    loader=FileSystemLoader(WEB_TEMPLATE_DIR),
    autoescape=select_autoescape(["html", "xml"]),
)

app = FastAPI(title="sosreport Structure Diagnostic")


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    template = env.get_template("index.html.j2")
    return HTMLResponse(template.render())


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/reports", response_class=HTMLResponse)
async def create_report(
    request: Request,
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
    output_format: Annotated[str, Form("html")],
) -> HTMLResponse:
    job_id = uuid.uuid4().hex[:12]
    job_upload_dir = UPLOAD_DIR / job_id
    job_output_dir = OUTPUT_DIR / job_id
    job_upload_dir.mkdir(parents=True, exist_ok=True)
    job_output_dir.mkdir(parents=True, exist_ok=True)

    saved_files: list[str] = []
    for upload in sosreports:
        safe_name = Path(upload.filename or "sosreport").name
        target = job_upload_dir / safe_name
        with target.open("wb") as fh:
            shutil.copyfileobj(upload.file, fh)
        saved_files.append(safe_name)

    metadata = {
        "customer_name": customer_name,
        "execution_period": execution_period,
        "location": location,
        "customer_contact": customer_contact,
        "sales": {
            "name": sales_name,
            "role": sales_role,
            "phone": sales_phone,
            "email": sales_email,
        },
        "engineers": [
            {
                "name": engineer_name,
                "role": engineer_role,
                "phone": engineer_phone,
                "email": engineer_email,
            }
        ],
    }

    # Integration point for Claude implementation:
    # 1. extract archives safely
    # 2. parse each sosreport
    # 3. evaluate YAML rules
    # 4. aggregate a DiagnosticReport
    # 5. render HTML and/or DOCX
    #
    # For now this runnable skeleton writes a simple HTML receipt so the
    # container/upload/download workflow can be validated independently.
    generated: list[dict[str, str]] = []
    if output_format in {"html", "both"}:
        html_path = job_output_dir / "structure-diagnostic.html"
        html_path.write_text(
            _placeholder_html(job_id, metadata, saved_files), encoding="utf-8"
        )
        generated.append(
            {
                "name": html_path.name,
                "url": f"/reports/{job_id}/{html_path.name}",
            }
        )

    # DOCX generation is intentionally deferred until the approved report
    # template and diagnostic engine are wired in. The UI exposes the option
    # now so the endpoint contract does not need to change later.
    if output_format in {"docx", "both"}:
        generated.append(
            {
                "name": "structure-diagnostic.docx (implementation pending)",
                "url": "",
            }
        )

    template = env.get_template("result.html.j2")
    return HTMLResponse(
        template.render(
            job_id=job_id,
            customer_name=customer_name,
            uploaded=saved_files,
            generated=generated,
        )
    )


@app.get("/reports/{job_id}/{filename}")
def download_report(job_id: str, filename: str) -> FileResponse:
    safe_job = Path(job_id).name
    safe_name = Path(filename).name
    target = OUTPUT_DIR / safe_job / safe_name
    return FileResponse(target, filename=safe_name)


def _placeholder_html(job_id: str, metadata: dict, uploaded: list[str]) -> str:
    rows = "".join(f"<li>{name}</li>" for name in uploaded)
    return f"""<!doctype html>
<html lang=\"ko\">
<head><meta charset=\"utf-8\"><title>Structure Diagnostic</title></head>
<body>
<h1>sosreport Structure Diagnostic</h1>
<p><strong>Job ID:</strong> {job_id}</p>
<p><strong>Customer:</strong> {metadata['customer_name']}</p>
<p><strong>Period:</strong> {metadata['execution_period']}</p>
<p><strong>Location:</strong> {metadata['location']}</p>
<h2>Uploaded sosreports</h2>
<ul>{rows}</ul>
<p>This is a web/container workflow placeholder. Diagnostic parser and final RockPLACE report rendering will replace this body.</p>
</body>
</html>
"""


def main() -> None:
    import uvicorn

    uvicorn.run("sosdiag.web.app:app", host="0.0.0.0", port=8000)
