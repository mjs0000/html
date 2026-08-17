from __future__ import annotations

from sosdiag.model.diagnostic import DiagnosticResult
from sosdiag.model.report import CustomerInfo, ReportMetadata
from sosdiag.renderer.html import render_html
from sosdiag.reporting import build_report


def test_render_corpus_summary_and_hosts(tmp_path):
    payloads = [
        {
            "source": "sosreport-host-a.tar.xz",
            "host": {
                "hostname": "host-a",
                "host_type": "physical",
                "product_name": "PowerEdge",
                "rhel_version": "9.6",
            },
            "diagnostics": [
                DiagnosticResult(
                    id="SYS_LIFECYCLE",
                    category="System",
                    section="3.2",
                    title="Life-Cycle",
                    status="PASS",
                    summary="supported",
                ).model_dump()
            ],
        },
        {
            "source": "sosreport-host-b.tar.xz",
            "host": {
                "hostname": "host-b",
                "host_type": "virtual",
                "product_name": "VMware20,1",
                "rhel_version": "9.2",
            },
            "diagnostics": [
                DiagnosticResult(
                    id="SYS_TIME_SYNC",
                    category="System",
                    section="3.8",
                    title="시간 동기화",
                    status="WARN",
                    summary="source count low",
                ).model_dump()
            ],
        },
    ]
    summary = {
        "source_count": 2,
        "analyzed_count": 2,
        "error_count": 0,
        "status_distribution": {
            "SYS_LIFECYCLE": {"PASS": 1, "WARN": 0, "FAIL": 0, "SKIPPED": 0},
            "SYS_TIME_SYNC": {"PASS": 0, "WARN": 1, "FAIL": 0, "SKIPPED": 0},
        },
        "errors": [],
    }
    report = build_report(
        payloads,
        ReportMetadata(customer=CustomerInfo(name="Test Customer")),
        run_summary=summary,
    )

    output = render_html(report, tmp_path / "report.html")
    html = output.read_text(encoding="utf-8")

    assert "Test Customer" in html
    assert "입력 sosreport" in html
    assert "SYS_TIME_SYNC" in html
    assert "host-a" in html
    assert "host-b" in html
    assert "VM" in html
    assert "WARN" in html
