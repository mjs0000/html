from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

from sosdiag.runner import analyze_source


_STATUS_ORDER = ("PASS", "WARN", "FAIL", "SKIPPED")
_ISSUE_STATUSES = {"WARN", "FAIL"}


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
    payloads: list[dict] = []
    by_diagnostic: dict[str, Counter[str]] = defaultdict(Counter)
    issue_distribution: dict[str, dict[str, dict[str, object]]] = defaultdict(dict)
    errors: list[dict] = []

    for source in sources:
        try:
            result = analyze_source(source)
        except Exception as exc:  # batch mode must continue across bad archives
            errors.append({"source": str(source), "error": f"{type(exc).__name__}: {exc}"})
            continue

        payloads.append(result)
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

            if status in _ISSUE_STATUSES:
                for issue_key, issue_status in _structured_issue_statuses(item):
                    aggregate = issue_distribution[diagnostic_id].setdefault(
                        issue_key,
                        {"warn_count": 0, "fail_count": 0, "hosts": []},
                    )
                    count_key = "warn_count" if issue_status == "WARN" else "fail_count"
                    aggregate[count_key] = int(aggregate[count_key]) + 1
                    host_list = aggregate["hosts"]
                    if isinstance(host_list, list) and hostname not in host_list:
                        host_list.append(hostname)

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

    normalized_issues: dict[str, dict[str, dict[str, object]]] = {}
    for diagnostic_id, issues in sorted(issue_distribution.items()):
        normalized_issues[diagnostic_id] = {}
        for issue_key, aggregate in sorted(issues.items()):
            normalized_issues[diagnostic_id][issue_key] = {
                "warn_count": int(aggregate["warn_count"]),
                "fail_count": int(aggregate["fail_count"]),
                "hosts": sorted(aggregate["hosts"], key=str.lower),
            }

    return {
        "source_count": len(hosts) + len(errors),
        "analyzed_count": len(hosts),
        "error_count": len(errors),
        "status_distribution": distribution,
        "issue_distribution": normalized_issues,
        "hosts": hosts,
        "payloads": payloads,
        "errors": errors,
    }


def _structured_issue_statuses(item: dict) -> list[tuple[str, str]]:
    current_values = item.get("current_values") or {}
    found: set[tuple[str, str]] = set()

    for key, value in current_values.items():
        if isinstance(value, str) and key.endswith("_status") and value in _ISSUE_STATUSES:
            found.add((key, value))
            continue

        if isinstance(value, dict) and key.endswith("_status"):
            for child_key, child_value in value.items():
                if isinstance(child_value, str) and child_value in _ISSUE_STATUSES:
                    found.add((str(child_key), child_value))

    return sorted(found)
