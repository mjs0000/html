from __future__ import annotations

from sosdiag.model.diagnostic import DiagnosticResult, Evidence
from sosdiag.model.facts import SelinuxFacts


def evaluate_selinux(facts: SelinuxFacts) -> DiagnosticResult:
    if not facts.has_usable_state:
        return DiagnosticResult(
            id="SYS_SELINUX",
            category="System",
            section="3.6",
            title="SELINUX",
            status="SKIPPED",
            grade=None,
            summary="SELinux 상태를 판정할 수 있는 유효한 Evidence가 없습니다.",
            include_in_report=False,
        )

    effective_mode = facts.runtime_mode or facts.configured_mode
    if effective_mode == "Disabled":
        status = "PASS"
        grade = "A"
        summary = "SELinux가 권고 상태인 disabled로 확인되었습니다."
    else:
        status = "WARN"
        grade = "B"
        summary = f"SELinux 현재 상태는 {effective_mode}이며, 권고 상태는 disabled입니다."

    findings: list[str] = []
    if facts.runtime_config_mismatch:
        findings.append("Runtime 상태와 /etc/selinux/config 설정이 일치하지 않습니다.")

    evidence: list[Evidence] = []
    if facts.runtime_mode is not None:
        evidence.append(Evidence(source=facts.runtime_source or "runtime", detail=f"runtime_mode={facts.runtime_mode}"))
    if facts.configured_mode is not None:
        evidence.append(Evidence(source=facts.configured_source or "config", detail=f"configured_mode={facts.configured_mode}"))

    return DiagnosticResult(
        id="SYS_SELINUX",
        category="System",
        section="3.6",
        title="SELINUX",
        status=status,
        grade=grade,
        value=effective_mode,
        summary=summary,
        findings=findings,
        current_values={
            "runtime_mode": facts.runtime_mode,
            "configured_mode": facts.configured_mode,
            "runtime_config_mismatch": facts.runtime_config_mismatch,
        },
        recommended_values={"state": "disabled"},
        recommendations=["SELinux 권고 상태는 disabled입니다."],
        evidence=evidence,
    )
