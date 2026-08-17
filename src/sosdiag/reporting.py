from __future__ import annotations

from pathlib import Path

import yaml

from sosdiag.model.diagnostic import DiagnosticResult, HostReport
from sosdiag.model.report import CustomerInfo, DiagnosticReport, ReportMetadata, ReportRunSummary


def load_report_metadata(path: str | Path | None = None) -> ReportMetadata:
    if path is None:
        return ReportMetadata(customer=CustomerInfo(name="-"))
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return ReportMetadata.model_validate(data)


def build_report(
    payloads: list[dict],
    metadata: ReportMetadata,
    run_summary: dict | None = None,
) -> DiagnosticReport:
    hosts: list[HostReport] = []
    for payload in payloads:
        host_data = payload.get("host", {})
        diagnostics = [DiagnosticResult.model_validate(item) for item in payload.get("diagnostics", [])]
        hosts.append(
            HostReport(
                hostname=host_data.get("hostname") or Path(payload.get("source", "unknown")).name,
                system_type=host_data.get("host_type"),
                hardware_model=host_data.get("product_name"),
                os_version=host_data.get("rhel_version"),
                diagnostics=diagnostics,
            )
        )

    hosts.sort(key=lambda host: (host.hostname or "").lower())
    parsed_summary = ReportRunSummary.model_validate(run_summary) if run_summary is not None else None
    return DiagnosticReport(metadata=metadata, hosts=hosts, run_summary=parsed_summary)


def corpus_run_summary(payload: dict) -> dict:
    return {
        "source_count": payload.get("source_count", 0),
        "analyzed_count": payload.get("analyzed_count", 0),
        "error_count": payload.get("error_count", 0),
        "status_distribution": payload.get("status_distribution", {}),
        "errors": payload.get("errors", []),
    }
