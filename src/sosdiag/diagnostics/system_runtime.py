from __future__ import annotations

from sosdiag.model.diagnostic import DiagnosticResult, Evidence, ReportTable
from sosdiag.model.system_runtime import ChronyFacts, FirewalldFacts, KdumpFacts, PackageUpdateFacts


def evaluate_package_update(facts: PackageUpdateFacts) -> DiagnosticResult:
    evidence = [Evidence(source=path, detail="kernel package evidence") for path in facts.evidence_paths]
    if not facts.reference_version:
        return DiagnosticResult(
            id="SYS_PACKAGE_UPDATE",
            category="System",
            section="3.5",
            title="주요 패키지 업데이트",
            status="SKIPPED",
            summary="신뢰 가능한 Red Hat 외부 Kernel 기준 버전이 없어 판정을 보류합니다.",
            current_values={
                "rhel_major": facts.rhel_major,
                "architecture": facts.architecture,
                "running_kernel": facts.running_kernel,
                "newest_installed_kernel": facts.newest_installed_kernel,
            },
            include_in_report=False,
            evidence=evidence,
        )
    findings: list[str] = []
    if facts.running_kernel and facts.newest_installed_kernel and facts.running_kernel not in facts.newest_installed_kernel:
        findings.append("현재 Running Kernel과 최신 설치 Kernel이 다릅니다. 재부팅 필요 여부를 확인하십시오.")
    return DiagnosticResult(
        id="SYS_PACKAGE_UPDATE",
        category="System",
        section="3.5",
        title="주요 패키지 업데이트",
        status="WARN" if findings else "PASS",
        summary="외부 Red Hat 기준 버전이 주입된 경우에만 Kernel 상태를 평가합니다.",
        findings=findings,
        current_values=facts.model_dump(),
        recommended_values={"reference_version": facts.reference_version},
        evidence=evidence,
    )


def evaluate_firewalld(facts: FirewalldFacts) -> DiagnosticResult:
    evidence = [Evidence(source=path, detail="firewalld state evidence") for path in facts.evidence_paths]
    if facts.enabled is None and facts.active is None:
        return DiagnosticResult(
            id="SYS_FIREWALLD", category="System", section="3.7", title="Firewalld",
            status="SKIPPED", summary="Firewalld 상태를 확인할 수 없습니다.", include_in_report=False, evidence=evidence,
        )
    status = "WARN" if facts.enabled is True or facts.active is True else "PASS"
    return DiagnosticResult(
        id="SYS_FIREWALLD", category="System", section="3.7", title="Firewalld", status=status,
        summary="Firewalld 비활성/비활성화 권고 기준으로 평가합니다.",
        current_values=facts.model_dump(), recommended_values={"enabled": False, "active": False}, evidence=evidence,
    )


def evaluate_chrony(facts: ChronyFacts) -> DiagnosticResult:
    evidence = [Evidence(source=path, detail="chrony evidence") for path in facts.evidence_paths]
    if facts.active is None or facts.configured_source_count is None:
        return DiagnosticResult(
            id="SYS_TIME_SYNC", category="System", section="3.8", title="시간 동기화",
            status="SKIPPED", summary="Chrony 서비스 상태 또는 Source 수를 확인할 수 없습니다.", include_in_report=False, evidence=evidence,
        )
    status = "PASS" if facts.active and facts.configured_source_count >= 4 else "WARN"
    findings = []
    if not facts.active:
        findings.append("chronyd가 Active 상태가 아닙니다.")
    if facts.configured_source_count < 4:
        findings.append(f"Configured Time Source가 {facts.configured_source_count}개로 권고값 4개 미만입니다.")
    return DiagnosticResult(
        id="SYS_TIME_SYNC", category="System", section="3.8", title="시간 동기화", status=status,
        summary="chronyd Active 및 Time Source 4개 이상 여부를 평가합니다.", findings=findings,
        current_values=facts.model_dump(), recommended_values={"active": True, "configured_source_count_min": 4}, evidence=evidence,
    )


def evaluate_kdump(facts: KdumpFacts) -> DiagnosticResult:
    evidence = [Evidence(source=path, detail="kdump evidence") for path in facts.evidence_paths]
    reservation_known = facts.kexec_crash_size is not None or facts.crashkernel_parameter is not None
    state_known = facts.enabled is not None or facts.active is not None
    if not reservation_known and not state_known and not facts.parameters:
        return DiagnosticResult(
            id="SYS_KDUMP", category="System", section="3.9", title="덤프 수집(Kdump)",
            status="SKIPPED", summary="Kdump 상태를 평가할 Evidence가 없습니다.", include_in_report=False, evidence=evidence,
        )

    reservation_ok = (facts.kexec_crash_size or 0) > 0 or bool(facts.crashkernel_parameter)
    if facts.active is False or facts.enabled is False or (reservation_known and not reservation_ok):
        kdump_status = "WARN"
    elif facts.active is True and reservation_known and reservation_ok:
        kdump_status = "PASS"
    else:
        kdump_status = "SKIPPED"

    recommended = {
        "kernel.nmi_watchdog": 0,
        "kernel.panic_on_io_nmi": 1,
        "kernel.panic_on_unrecovered_nmi": 1,
        "kernel.unknown_nmi_panic": 1,
        "kernel.sysrq": 1,
    }
    present = [name for name in recommended if name in facts.parameters]
    missing = [name for name in recommended if name not in facts.parameters]
    mismatched = [name for name in present if facts.parameters[name] != recommended[name]]
    if mismatched:
        parameter_status = "WARN"
    elif missing:
        parameter_status = "SKIPPED"
    else:
        parameter_status = "PASS"

    visible = [status for status in (kdump_status, parameter_status) if status != "SKIPPED"]
    overall = "WARN" if "WARN" in visible else ("PASS" if len(visible) == 2 and all(s == "PASS" for s in visible) else "SKIPPED")
    rows = [
        {
            "parameter": name,
            "value": facts.parameters.get(name),
            "recommended": recommended.get(name),
            "display_only": name not in recommended,
        }
        for name in facts.parameters
    ]
    return DiagnosticResult(
        id="SYS_KDUMP", category="System", section="3.9", title="덤프 수집(Kdump)", status=overall,
        summary="Kdump State와 관련 Kernel Parameter를 별도 상태로 평가합니다.",
        current_values={
            **facts.model_dump(),
            "kdump_status": kdump_status,
            "kernel_parameter_status": parameter_status,
            "missing_required_parameters": missing,
        },
        recommended_values=recommended, evidence=evidence,
        tables=[ReportTable(columns=["parameter", "value", "recommended", "display_only"], rows=rows)] if rows else [],
        include_in_report=overall != "SKIPPED",
    )
