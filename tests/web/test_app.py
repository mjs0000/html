from __future__ import annotations

import io
import tarfile

from fastapi.testclient import TestClient

from sosdiag.web import app as web_app


def _archive_bytes(hostname: str) -> bytes:
    buffer = io.BytesIO()
    root = f"sosreport-{hostname}"
    with tarfile.open(fileobj=buffer, mode="w") as tf:
        files = {
            "hostname": f"{hostname}\n",
            "etc/redhat-release": "Red Hat Enterprise Linux release 9.6 (Plow)\n",
            "sos_commands/hardware/dmidecode": "System Information\n\tManufacturer: Dell Inc.\n\tProduct Name: PowerEdge R760\n",
            "sos_commands/kernel/uname_-a": f"Linux {hostname} 5.14.0-570.12.1.el9_6.x86_64 #1 SMP x86_64 GNU/Linux\n",
            "sos_commands/selinux/sestatus": "SELinux status: disabled\n",
            "etc/selinux/config": "SELINUX=disabled\n",
        }
        for path, text in files.items():
            payload = text.encode()
            info = tarfile.TarInfo(f"{root}/{path}")
            info.size = len(payload)
            tf.addfile(info, io.BytesIO(payload))
    return buffer.getvalue()


def test_web_multi_upload_generates_html_and_json(tmp_path, monkeypatch) -> None:
    upload_dir = tmp_path / "uploads"
    output_dir = tmp_path / "output"
    upload_dir.mkdir()
    output_dir.mkdir()
    monkeypatch.setattr(web_app, "UPLOAD_DIR", upload_dir)
    monkeypatch.setattr(web_app, "OUTPUT_DIR", output_dir)

    client = TestClient(web_app.app)
    response = client.post(
        "/reports",
        data={
            "customer_name": "Example Customer",
            "execution_period": "2026.08.01 ~ 2026.08.05",
            "location": "Seoul",
            "customer_contact": "Customer User",
            "sales_name": "Sales User",
            "engineer_name": "Engineer User",
        },
        files=[
            ("sosreports", ("sosreport-host-a.tar", _archive_bytes("host-a"), "application/x-tar")),
            ("sosreports", ("sosreport-host-b.tar", _archive_bytes("host-b"), "application/x-tar")),
        ],
    )

    assert response.status_code == 200
    assert "구조진단 실행 완료" in response.text
    assert "분석 완료 Host" in response.text
    assert "report.html" in response.text
    assert "corpus-analysis.json" in response.text

    job_dirs = list(output_dir.iterdir())
    assert len(job_dirs) == 1
    report_html = job_dirs[0] / "report.html"
    analysis_json = job_dirs[0] / "corpus-analysis.json"
    assert report_html.is_file()
    assert analysis_json.is_file()

    html = report_html.read_text(encoding="utf-8")
    assert "host-a" in html
    assert "host-b" in html
    assert "Hardware Certification" in html


def test_web_rejects_non_sosreport_filename(tmp_path, monkeypatch) -> None:
    upload_dir = tmp_path / "uploads"
    output_dir = tmp_path / "output"
    upload_dir.mkdir()
    output_dir.mkdir()
    monkeypatch.setattr(web_app, "UPLOAD_DIR", upload_dir)
    monkeypatch.setattr(web_app, "OUTPUT_DIR", output_dir)

    client = TestClient(web_app.app)
    response = client.post(
        "/reports",
        data={
            "customer_name": "Example Customer",
            "execution_period": "2026.08.01",
            "location": "Seoul",
        },
        files=[("sosreports", ("not-a-sosreport.txt", b"bad", "text/plain"))],
    )

    assert response.status_code == 400
