from __future__ import annotations

from sosdiag.model.diagnostic import DiagnosticResult, Evidence
from sosdiag.model.facts import SelinuxFacts


def evaluate_selinux(facts: SelinuxFacts) -> DiagnosticResult:
    findings: list[str] = []
    evidence: list[Evidence] = []

    if facts.runtime_mode is not None:
        evidence.append(
            Evidence(
                source=facts.runtime_source or "getenforce",
                detail=f"runtime_mode={facts.runtime_mode}",
            )
        )
    else:
        findings.append("getenforce Runtime 상태 Evidence가 없습니다.")

    if facts.configured_mode is not None:
        evidence.append(
            Evidence(
                source=facts.configured_source or "/etc/selinux/config",
                detail=f"configured_mode={facts.configured_mode}",
            )
        )
    else:
        findings.append("/etc/selinux/config 설정 상태 Evidence가 없습니다.")

    if facts.kernel_cmdline is not None:
        evidence.append(
            Evidence(
                source=facts.kernel_cmdline_source or "/proc/cmdline",
                detail=f"selinux=0_present={facts.kernel_selinux_disabled}; cmdline={facts.kernel_cmdline}",
            )
        )

    if not facts.has_usable_state:
        return DiagnosticResult(
            id="SYS_SELINUX",
            category="System",
            section="3.6",
            title="SELINUX",
            status="SKIPPED",
            summary="getenforce와 /etc/selinux/config에서 SELinux 상태를 확인할 수 없습니다.",
            findings=findings,
            include_in_report=False,
            evidence=evidence,
        )

    primary_modes = [mode for mode in (facts.runtime_mode, facts.configured_mode) if mode is not None]
    if all(mode == "Disabled" for mode in primary_modes):
        status = "PASS"
        summary = "SELinux Runtime/Configuration의 주요 Evidence가 disabled 권고 상태와 일치합니다."
    else:
        status = "WARN"
        summary = "SELinux Runtime 또는 Configuration이 disabled 권고 상태와 일치하지 않습니다."

    if facts.runtime_config_mismatch:
        findings.append("Runtime 상태와 /etc/selinux/config 설정이 일치하지 않습니다.")

    # /proc/cmdline is additional evidence only. It never independently overrides
    # the primary decision made from getenforce + /etc/selinux/config.
    if facts.rhel_major is not None and facts.rhel_major >= 9 and facts.kernel_selinux_disabled is False:
        findings.append(
            "RHEL 9 이상이며 /proc/cmdline에 selinux=0이 없습니다. 주요 판정은 getenforce와 /etc/selinux/config를 따르되 추가 검토가 필요합니다."
        )
    if facts.kernel_selinux_disabled is True and facts.runtime_mode not in {None, "Disabled"}:
        findings.append(
            "/proc/cmdline에는 selinux=0이 있으나 Runtime 상태와 일치하지 않습니다. Evidence 충돌을 확인해야 합니다."
        )

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
        recommended_values={"state": "disabled"},
        recommendations=[
            "SELinux 권고 상태는 disabled입니다.",
            "주요 판정은 getenforce와 /etc/selinux/config를 기준으로 수행합니다.",
            "/proc/cmdline은 추가 Evidence로 표시하며 RHEL 9 이상에서는 selinux=0 여부를 함께 검토합니다.",
        ],
        evidence=evidence,
    )
