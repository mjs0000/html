from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

from sosdiag.runner import analyze_source


_STATUS_ORDER = ("PASS", "WARN", "FAIL", "SKIPPED")


def discover_sosreports(root: str | Path) -> list[Path]:
    base = Path(root)
    if not base.exists():
        raise FileNotFoundError(base)
    if base.is_file():
        return [base]
    return sorted(
        path
        for path in base.iterdir()
        if path.is_file() and path.name.startswith("sosreport-") and ".tar" in path.name
    )


def analyze_corpus(sources: Iterable[str | Path]) -> dict:
    hosts: list[dict] = []
    by_diagnostic: dict[str, Counter[str]] = defaultdict(Counter)
    errors: list[dict] = []

    for source in sources:
        try:
            result = analyze_source(source)
        except Exception as exc:  # batch mode must continue across bad archives
            errors.append({"source": str(source), "error": f"{type(exc).__name__}: {exc}"})
            continue

        hostname = result.get("host", {}).get("hostname") or Path(source).name
        diagnostics = result.get("diagnostics", [])
        compact = []
        for item in diagnostics:
            diagnostic_id = item.get("id", "UNKNOWN")
            status = item.get("status", "SKIPPED")
            by_diagnostic[diagnostic_id][status] += 1
            compact.append({
                "id": diagnostic_id,
                "section": item.get("section"),
                "title": item.get("title"),
                "status": status,
                "summary": item.get("summary"),
                "include_in_report": item.get("include_in_report", True),
            })
        hosts.append({
            "source": str(source),
            "hostname": hostname,
            "rhel_version": result.get("host", {}).get("rhel_version"),
            "host_type": result.get("host", {}).get("host_type"),
            "diagnostics": compact,
        })

    distribution = {}
    for diagnostic_id, counts in sorted(by_diagnostic.items()):
        distribution[diagnostic_id] = {status: counts.get(status, 0) for status in _STATUS_ORDER}

    return {
        "source_count": len(hosts) + len(errors),
        "analyzed_count": len(hosts),
        "error_count": len(errors),
        "status_distribution": distribution,
        "hosts": hosts,
        "errors": errors,
    }
