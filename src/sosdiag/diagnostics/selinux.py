from __future__ import annotations

from sosdiag.model.diagnostic import DiagnosticResult, Evidence
from sosdiag.model.facts import SelinuxFacts


def evaluate_selinux(facts: SelinuxFacts) -> DiagnosticResult:
    findings: list[str] = []
    evidence: list[Evidence] = []

    if facts.runtime_mode is not None:
        evidence.append(
            Evidence(
                source=facts.runtime_source or "runtime",
                detail=f"runtime_mode={facts.runtime_mode}",
            )
        )
    if facts.configured_mode is not None:
        evidence.append(
            Evidence(
                source=facts.configured_source or "config",
                detail=f"configured_mode={facts.configured_mode}",
            )
        )
    if facts.kernel_cmdline is not None:
        evidence.append(
            Evidence(
                source=facts.kernel_cmdline_source or "/proc/cmdline",
                detail=f"selinux=0_present={facts.kernel_selinux_disabled}; cmdline={facts.kernel_cmdline}",
            )
        )

    if facts.rhel_major is None:
        return DiagnosticResult(
            id="SYS_SELINUX",
            category="System",
            section="3.6",
            title="SELINUX",
            status="SKIPPED",
            summary="RHEL major version을 확인할 수 없어 SELinux 버전별 정책을 적용할 수 없습니다.",
            findings=["OS version evidence가 필요합니다."],
            include_in_report=False,
            evidence=evidence,
        )

    if facts.rhel_major >= 9:
        if facts.kernel_selinux_disabled is None:
            return DiagnosticResult(
                id="SYS_SELINUX",
                category="System",
                section="3.6",
                title="SELINUX",
                status="SKIPPED",
                summary="RHEL 9 이상에서는 /proc/cmdline 확인이 필요하지만 해당 Evidence가 없습니다.",
                findings=["/proc/cmdline에서 selinux=0 존재 여부를 확인할 수 없습니다."],
                include_in_report=False,
                current_values={
                    "rhel_major": facts.rhel_major,
                    "runtime_mode": facts.runtime_mode,
                    "configured_mode": facts.configured_mode,
                    "kernel_selinux_disabled": facts.kernel_selinux_disabled,
                },
                recommended_values={"kernel_parameter": "selinux=0"},
                evidence=evidence,
            )

        if facts.kernel_selinux_disabled:
            status = "PASS"
            summary = "RHEL 9 이상이며 /proc/cmdline에서 selinux=0이 확인되었습니다."
            if facts.runtime_mode not in {None, "Disabled"}:
                status = "WARN"
                findings.append(
                    "커널 명령행에는 selinux=0이 있으나 수집된 Runtime 상태와 일치하지 않습니다. Evidence 확인이 필요합니다."
                )
        else:
            status = "WARN"
            summary = "RHEL 9 이상이지만 /proc/cmdline에서 selinux=0이 확인되지 않았습니다."
            findings.append("RHEL 9 SELinux 비활성화 정책 기준인 selinux=0이 커널 명령행에 없습니다.")
    else:
        effective_mode = facts.runtime_mode or facts.configured_mode
        if effective_mode is None:
            return DiagnosticResult(
                id="SYS_SELINUX",
                category="System",
                section="3.6",
                title="SELINUX",
                status="SKIPPED",
                summary="SELinux 상태를 판정할 수 있는 유효한 Evidence가 없습니다.",
                include_in_report=False,
                evidence=evidence,
            )
        if effective_mode == "Disabled":
            status = "PASS"
            summary = "SELinux가 권고 상태인 disabled로 확인되었습니다."
        else:
            status = "WARN"
            summary = f"SELinux 현재 상태는 {effective_mode}이며, 권고 상태는 disabled입니다."

    if facts.runtime_config_mismatch:
        findings.append("Runtime 상태와 /etc/selinux/config 설정이 일치하지 않습니다.")

    return DiagnosticResult(
        id="SYS_SELINUX",
        category="System",
        section="3.6",
        title="SELINUX",
        status=status,
        value=facts.runtime_mode or facts.configured_mode,
        summary=summary,
        findings=findings,
        current_values={
            "rhel_major": facts.rhel_major,
            "runtime_mode": facts.runtime_mode,
            "configured_mode": facts.configured_mode,
            "runtime_config_mismatch": facts.runtime_config_mismatch,
            "kernel_selinux_disabled": facts.kernel_selinux_disabled,
            "kernel_cmdline": facts.kernel_cmdline,
        },
        recommended_values={
            "state": "disabled",
            "rhel_9_plus_kernel_parameter": "selinux=0",
        },
        recommendations=[
            "SELinux 권고 상태는 disabled입니다.",
            "RHEL 9 이상에서는 /proc/cmdline에 selinux=0이 적용되어 있는지 확인합니다.",
        ],
        evidence=evidence,
    )
