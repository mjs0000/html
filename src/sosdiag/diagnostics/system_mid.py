from __future__ import annotations

from sosdiag.model.diagnostic import DiagnosticResult, ReportTable
from sosdiag.model.system_mid import (
    CoreDumpFacts,
    DefaultServiceFacts,
    ErrorLogFacts,
    KernelParameterFacts,
    LogrotateSysstatFacts,
)


def evaluate_error_log(facts: ErrorLogFacts) -> DiagnosticResult:
    if not facts.usable_sources:
        return DiagnosticResult(
            id="SYS_ERROR_LOG", category="System", section="3.10", title="시스템 에러 로그",
            status="SKIPPED", summary="사용 가능한 messages/dmesg/journal Evidence가 없습니다.", include_in_report=False,
        )
    fail = [f for f in facts.findings if f.severity == "FAIL"]
    warn = [f for f in facts.findings if f.severity == "WARN"]
    status = "FAIL" if fail else ("WARN" if warn else "PASS")
    rows = [f.model_dump() for f in facts.findings]
    return DiagnosticResult(
        id="SYS_ERROR_LOG", category="System", section="3.10", title="시스템 에러 로그", status=status,
        summary="Context-aware signature filtering 결과입니다.",
        findings=[f"{f.signature}: {f.count}회" for f in facts.findings],
        current_values={"critical_count": len(fail), "warning_count": len(warn)},
        tables=[ReportTable(columns=["source", "severity", "signature", "count", "message"], rows=rows)],
    )


def evaluate_kernel_parameters(facts: KernelParameterFacts) -> DiagnosticResult:
    if not facts.evidence_paths:
        return DiagnosticResult(
            id="SYS_KERNEL_PARAM", category="System", section="3.11", title="기본 커널 파라미터",
            status="SKIPPED", summary="sysctl Evidence가 없습니다.", include_in_report=False,
        )
    recs = {
        "vm.dirty_background_ratio": ("eq", 10),
        "vm.dirty_ratio": ("eq", 30 if facts.host_type == "virtual" else 40),
        "vm.swappiness": ("range", (1, 10)),
        "net.core.somaxconn": ("ge", 4096),
        "net.ipv4.tcp_max_syn_backlog": ("ge", 8192),
    }
    findings: list[str] = []
    rows = []
    statuses: list[str] = []
    for name, rule in recs.items():
        value = facts.values.get(name)
        if value is None:
            st = "SKIPPED"
        else:
            op, target = rule
            ok = value == target if op == "eq" else (target[0] <= value <= target[1] if op == "range" else value >= target)
            st = "PASS" if ok else "WARN"
            if not ok:
                findings.append(f"{name}={value} 권장 기준 미충족")
        statuses.append(st)
        rows.append({"parameter": name, "value": value, "status": st})

    ipf = facts.values.get("net.ipv4.ip_forward")
    ipf_status = "SKIPPED" if facts.nat_workload is None or ipf is None else ("PASS" if ipf == (1 if facts.nat_workload else 0) else "WARN")
    statuses.append(ipf_status)
    rows.append({"parameter": "net.ipv4.ip_forward", "value": ipf, "status": ipf_status})

    overall = "WARN" if "WARN" in statuses else ("PASS" if any(s == "PASS" for s in statuses) else "SKIPPED")
    return DiagnosticResult(
        id="SYS_KERNEL_PARAM", category="System", section="3.11", title="기본 커널 파라미터", status=overall,
        summary="프로젝트 기본 커널 파라미터 기준 비교 결과입니다.", findings=findings,
        tables=[ReportTable(columns=["parameter", "value", "status"], rows=rows)],
        include_in_report=overall != "SKIPPED",
    )


def evaluate_default_services(facts: DefaultServiceFacts) -> DiagnosticResult:
    if not facts.evidence_paths:
        return DiagnosticResult(
            id="SYS_DEFAULT_SERVICE", category="System", section="3.12", title="Default Service Enabled",
            status="SKIPPED", summary="systemd Evidence가 없습니다.", include_in_report=False,
        )
    rows = []
    statuses = []
    findings = []
    for name, state in facts.services.items():
        if state.enabled is None and state.active is None:
            st = "SKIPPED"
        elif state.enabled is True or state.active is True:
            st = "WARN"
            findings.append(f"{name} enabled/active 상태 확인")
        else:
            st = "PASS"
        statuses.append(st)
        rows.append({"service": name, "enabled": state.enabled, "active": state.active, "status": st})
    overall = "WARN" if "WARN" in statuses else ("PASS" if any(s == "PASS" for s in statuses) else "SKIPPED")
    return DiagnosticResult(
        id="SYS_DEFAULT_SERVICE", category="System", section="3.12", title="Default Service Enabled", status=overall,
        summary="12개 unconditional disable 대상 서비스만 평가합니다.", findings=findings,
        tables=[ReportTable(columns=["service", "enabled", "active", "status"], rows=rows)],
        include_in_report=overall != "SKIPPED",
    )


def evaluate_coredump(facts: CoreDumpFacts) -> DiagnosticResult:
    sub = {}
    if facts.hard_core_limit is None and facts.soft_core_limit is None and facts.limits_soft_unlimited is None:
        sub["core_limit"] = "SKIPPED"
    elif str(facts.hard_core_limit).lower() == "unlimited" and str(facts.soft_core_limit).lower() == "unlimited":
        sub["core_limit"] = "PASS"
    elif facts.limits_soft_unlimited and facts.limits_hard_unlimited:
        sub["core_limit"] = "PASS"
    else:
        sub["core_limit"] = "WARN"

    if "etc/systemd/system.conf" not in facts.evidence_paths:
        sub["default_limit_core"] = "SKIPPED"
    else:
        sub["default_limit_core"] = "PASS" if str(facts.default_limit_core).lower() == "infinity" else "WARN"

    sub["retention"] = "SKIPPED" if facts.retention_override is None else ("PASS" if facts.retention_override else "WARN")
    visible = list(sub.values())
    overall = "WARN" if "WARN" in visible else ("PASS" if any(s == "PASS" for s in visible) else "SKIPPED")
    return DiagnosticResult(
        id="SYS_APP_COREDUMP", category="System", section="3.13", title="Application Core Dump", status=overall,
        summary="Core Limit / DefaultLimitCORE / Retention을 별도 평가합니다.",
        current_values={**facts.model_dump(), "sub_status": sub}, include_in_report=overall != "SKIPPED",
    )


def evaluate_logrotate_sysstat(facts: LogrotateSysstatFacts) -> DiagnosticResult:
    freq = "SKIPPED" if facts.logrotate_frequency is None else ("PASS" if facts.logrotate_frequency in {"daily", "weekly"} else "WARN")
    retention = "SKIPPED" if facts.logrotate_rotate_count is None else ("PASS" if facts.logrotate_rotate_count >= 12 else "WARN")
    if facts.sysstat_installed is False:
        sar = "WARN"
    elif facts.sysstat_enabled is False:
        sar = "WARN"
    elif facts.sar_interval_minutes is None:
        sar = "SKIPPED"
    else:
        sar = "PASS" if facts.sar_interval_minutes == 1 else "WARN"
    statuses = [freq, retention, sar]
    overall = "WARN" if "WARN" in statuses else ("PASS" if all(s == "PASS" for s in statuses) else "SKIPPED")
    return DiagnosticResult(
        id="SYS_LOGROTATE_SYSSTAT", category="System", section="3.14", title="Logrotate / sysstat(SAR)", status=overall,
        summary="Logrotate Frequency / Retention / SAR Interval을 별도 평가합니다.",
        current_values={**facts.model_dump(), "frequency_status": freq, "retention_status": retention, "sar_status": sar},
        include_in_report=overall != "SKIPPED",
    )
