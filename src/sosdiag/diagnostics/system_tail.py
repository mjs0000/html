from __future__ import annotations

from sosdiag.model.diagnostic import DiagnosticResult, Evidence
from sosdiag.model.system_tail import IrqbalanceFacts, OtherSettingsFacts, TimerFacts, TunedFacts


def _worse(statuses: list[str]) -> str:
    order = {"PASS": 0, "SKIPPED": 1, "WARN": 2, "FAIL": 3}
    return max(statuses, key=lambda item: order[item]) if statuses else "SKIPPED"


def evaluate_tuned(facts: TunedFacts) -> DiagnosticResult:
    service_status = "SKIPPED" if facts.enabled is None or facts.active is None else (
        "PASS" if facts.enabled and facts.active else "WARN"
    )
    profile_status = "SKIPPED" if not facts.active_profile or not facts.recommended_profile else (
        "PASS" if facts.active_profile == facts.recommended_profile else "WARN"
    )
    overall = _worse([service_status, profile_status])
    return DiagnosticResult(
        id="SYS_TUNED",
        category="System",
        section="3.15",
        title="Tuned",
        status=overall,
        summary="Tuned 서비스와 시스템 유형별 권장 Profile을 각각 평가합니다.",
        current_values={
            "enabled": facts.enabled,
            "active": facts.active,
            "active_profile": facts.active_profile,
            "host_type": facts.host_type,
            "live_10g": facts.live_10g,
            "service_status": service_status,
            "profile_status": profile_status,
        },
        recommended_values={"profile": facts.recommended_profile},
        evidence=[Evidence(source=path, detail="tuned evidence") for path in facts.evidence_paths],
        include_in_report=overall != "SKIPPED",
    )


def evaluate_irqbalance(facts: IrqbalanceFacts) -> DiagnosticResult:
    service_status = "SKIPPED" if facts.enabled is None or facts.active is None else (
        "PASS" if facts.enabled and facts.active else "WARN"
    )
    oneshot_status = "SKIPPED" if facts.oneshot is None and not facts.evidence_paths else (
        "PASS" if (facts.oneshot or "").lower() == "yes" else "WARN"
    )
    overall = _worse([service_status, oneshot_status])
    return DiagnosticResult(
        id="SYS_IRQBALANCE",
        category="System",
        section="3.16",
        title="IRQ Balance Processing",
        status=overall,
        summary="irqbalance 서비스와 IRQBALANCE_ONESHOT 설정을 별도 평가합니다.",
        current_values={
            "enabled": facts.enabled,
            "active": facts.active,
            "oneshot": facts.oneshot,
            "service_status": service_status,
            "oneshot_status": oneshot_status,
        },
        recommended_values={"enabled": True, "active": True, "IRQBALANCE_ONESHOT": "yes"},
        evidence=[Evidence(source=path, detail="irqbalance evidence") for path in facts.evidence_paths],
        include_in_report=overall != "SKIPPED",
    )


def evaluate_timer(facts: TimerFacts) -> DiagnosticResult:
    if facts.enabled is None and facts.active is None:
        return DiagnosticResult(
            id="SYS_TIMER",
            category="System",
            section="3.17",
            title="Timer",
            status="SKIPPED",
            summary="dnf-makecache.timer 상태를 확인할 수 없습니다.",
            evidence=[Evidence(source=path, detail="timer evidence") for path in facts.evidence_paths],
            include_in_report=False,
        )
    status = "PASS" if facts.enabled is False and facts.active is False else "WARN"
    return DiagnosticResult(
        id="SYS_TIMER",
        category="System",
        section="3.17",
        title="Timer",
        status=status,
        summary="dnf-makecache.timer는 disabled/inactive 상태를 권장합니다.",
        current_values=facts.model_dump(),
        recommended_values={"enabled": False, "active": False},
        evidence=[Evidence(source=path, detail="dnf-makecache.timer evidence") for path in facts.evidence_paths],
    )


def evaluate_other_settings(facts: OtherSettingsFacts) -> DiagnosticResult:
    rsyslog_status = "SKIPPED" if facts.rsyslog_filter_present is None else (
        "PASS" if facts.rsyslog_filter_present else "WARN"
    )
    cron_status = "SKIPPED" if facts.cron_mailto_present is None else (
        "PASS" if facts.cron_mailto_present and facts.cron_mailto == "" else "WARN"
    )
    overall = _worse([rsyslog_status, cron_status])
    return DiagnosticResult(
        id="SYS_OTHER_SETTINGS",
        category="System",
        section="3.18",
        title="기타 설정 (rsyslog / cron)",
        status=overall,
        summary="rsyslog session/slice filter와 Cron MAILTO를 별도 평가합니다.",
        current_values={
            "rsyslog_filter_present": facts.rsyslog_filter_present,
            "cron_mailto": facts.cron_mailto,
            "cron_mailto_present": facts.cron_mailto_present,
            "rsyslog_status": rsyslog_status,
            "cron_status": cron_status,
        },
        recommended_values={"rsyslog_filter": True, "MAILTO": ""},
        evidence=[Evidence(source=path, detail="other settings evidence") for path in facts.evidence_paths],
        include_in_report=overall != "SKIPPED",
    )
