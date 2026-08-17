from __future__ import annotations

import re

from sosdiag.archive import SosArchive
from sosdiag.model.host import HostFacts
from sosdiag.model.system_tail import IrqbalanceFacts, OtherSettingsFacts, TimerFacts, TunedFacts
from sosdiag.parser.systemd import parse_systemd_unit_state


def _has_live_10g(archive: SosArchive) -> bool | None:
    ethtools = archive.glob_text("sos_commands/networking/ethtool_*")
    if not ethtools:
        return None
    saw_speed = False
    for path, text in ethtools:
        suffix = path.split("ethtool_", 1)[-1]
        if not suffix or suffix.startswith("-"):
            continue
        speed = re.search(r"Speed:\s*(\d+)Mb/s", text, re.I)
        link = re.search(r"Link detected:\s*yes", text, re.I)
        if speed:
            saw_speed = True
            if int(speed.group(1)) >= 10000 and link:
                return True
    return False if saw_speed else None


def parse_tuned_facts(archive: SosArchive, host: HostFacts) -> TunedFacts:
    state = parse_systemd_unit_state(archive, "tuned.service")
    facts = TunedFacts(
        enabled=state.enabled,
        active=state.active,
        host_type=host.host_type,
        evidence_paths=list(state.evidence_paths),
    )
    active_profile = archive.first_text([
        "sos_commands/tuned/tuned-adm_active",
        "etc/tuned/active_profile",
    ])
    if active_profile:
        facts.evidence_paths.append(active_profile[0])
        text = active_profile[1].strip()
        m = re.search(r"Current active profile:\s*(\S+)", text, re.I)
        facts.active_profile = m.group(1) if m else (text.splitlines()[0].strip() if text else None)

    facts.live_10g = _has_live_10g(archive)
    if host.host_type == "virtual":
        facts.recommended_profile = "virtual-guest"
    elif host.host_type == "physical" and facts.live_10g is False:
        facts.recommended_profile = "throughput-performance"
    elif host.host_type == "physical" and facts.live_10g is True:
        # network-throughput requires an additional non-DB/non-virtualization workload determination.
        # Sosreport network speed alone is insufficient, so leave the profile recommendation unresolved.
        facts.recommended_profile = None

    facts.evidence_paths = list(dict.fromkeys(facts.evidence_paths))
    return facts


def parse_irqbalance_facts(archive: SosArchive) -> IrqbalanceFacts:
    state = parse_systemd_unit_state(archive, "irqbalance.service")
    facts = IrqbalanceFacts(enabled=state.enabled, active=state.active, evidence_paths=list(state.evidence_paths))
    config = archive.read_text("etc/sysconfig/irqbalance")
    if config is not None:
        facts.evidence_paths.append("etc/sysconfig/irqbalance")
        for line in config.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            m = re.match(r"IRQBALANCE_ONESHOT\s*=\s*['\"]?([^'\"#\s]+)", stripped, re.I)
            if m:
                facts.oneshot = m.group(1)
                break
    facts.evidence_paths = list(dict.fromkeys(facts.evidence_paths))
    return facts


def parse_timer_facts(archive: SosArchive) -> TimerFacts:
    state = parse_systemd_unit_state(archive, "dnf-makecache.timer")
    facts = TimerFacts(enabled=state.enabled, active=state.active, evidence_paths=list(state.evidence_paths))
    timers = archive.first_text(["sos_commands/systemd/systemctl_list-timers_--all"])
    if timers:
        facts.evidence_paths.append(timers[0])
        facts.listed = "dnf-makecache.timer" in timers[1]
        if facts.active is None:
            facts.active = facts.listed
    facts.evidence_paths = list(dict.fromkeys(facts.evidence_paths))
    return facts


def parse_other_settings_facts(archive: SosArchive) -> OtherSettingsFacts:
    facts = OtherSettingsFacts()
    rsyslog = archive.read_text("etc/rsyslog.d/0-ignore-systemd-session-slice.conf")
    if rsyslog is not None:
        facts.evidence_paths.append("etc/rsyslog.d/0-ignore-systemd-session-slice.conf")
        lowered = rsyslog.lower()
        facts.rsyslog_filter_present = bool(
            ("session" in lowered or "slice" in lowered) and ("stop" in lowered or "~" in rsyslog)
        )
    else:
        all_rsyslog = archive.glob_text("etc/rsyslog.d/*")
        main_rsyslog = archive.read_text("etc/rsyslog.conf")
        if all_rsyslog or main_rsyslog is not None:
            facts.rsyslog_filter_present = False
            facts.evidence_paths.extend(path for path, _ in all_rsyslog)
            if main_rsyslog is not None:
                facts.evidence_paths.append("etc/rsyslog.conf")

    crontab = archive.read_text("etc/crontab")
    if crontab is not None:
        facts.evidence_paths.append("etc/crontab")
        facts.cron_mailto_present = False
        for line in crontab.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            m = re.match(r"MAILTO\s*=\s*(.*)$", stripped, re.I)
            if m:
                facts.cron_mailto_present = True
                facts.cron_mailto = m.group(1).strip().strip("'\"")
                break
    facts.evidence_paths = list(dict.fromkeys(facts.evidence_paths))
    return facts
