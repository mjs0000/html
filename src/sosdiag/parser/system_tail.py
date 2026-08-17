from __future__ import annotations

import re

from sosdiag.archive import SosArchive
from sosdiag.model.host import HostFacts
from sosdiag.model.system_tail import IrqbalanceFacts, OtherSettingsFacts, TimerFacts, TunedFacts


def _systemd_state(archive: SosArchive, unit: str) -> tuple[bool | None, bool | None, list[str]]:
    paths: list[str] = []
    enabled: bool | None = None
    active: bool | None = None
    unit_files = archive.first_text([
        "sos_commands/systemd/systemctl_list-unit-files",
        "sos_commands/systemd/systemctl_list-unit-files_--no-pager",
    ])
    units = archive.first_text([
        "sos_commands/systemd/systemctl_list-units",
        "sos_commands/systemd/systemctl_list-units_--all",
    ])
    if unit_files:
        paths.append(unit_files[0])
        m = re.search(rf"^{re.escape(unit)}\s+(enabled|disabled|masked|static|indirect)\b", unit_files[1], re.M)
        if m:
            enabled = m.group(1) == "enabled"
    if units:
        paths.append(units[0])
        m = re.search(rf"^{re.escape(unit)}\s+loaded\s+(active|inactive|failed)\b", units[1], re.M)
        if m:
            active = m.group(1) == "active"
    return enabled, active, paths


def _has_live_10g(archive: SosArchive) -> bool | None:
    ethtools = archive.glob_text("sos_commands/networking/ethtool_*")
    if not ethtools:
        return None
    saw_speed = False
    for _, text in ethtools:
        speed = re.search(r"Speed:\s*(\d+)Mb/s", text, re.I)
        link = re.search(r"Link detected:\s*yes", text, re.I)
        if speed:
            saw_speed = True
            if int(speed.group(1)) >= 10000 and link:
                return True
    return False if saw_speed else None


def parse_tuned_facts(archive: SosArchive, host: HostFacts) -> TunedFacts:
    enabled, active, paths = _systemd_state(archive, "tuned.service")
    facts = TunedFacts(enabled=enabled, active=active, host_type=host.host_type, evidence_paths=paths)
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
    elif host.host_type == "physical":
        facts.recommended_profile = "network-throughput" if facts.live_10g else "throughput-performance"
    return facts


def parse_irqbalance_facts(archive: SosArchive) -> IrqbalanceFacts:
    enabled, active, paths = _systemd_state(archive, "irqbalance.service")
    facts = IrqbalanceFacts(enabled=enabled, active=active, evidence_paths=paths)
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
    return facts


def parse_timer_facts(archive: SosArchive) -> TimerFacts:
    enabled, active, paths = _systemd_state(archive, "dnf-makecache.timer")
    facts = TimerFacts(enabled=enabled, active=active, evidence_paths=paths)
    timers = archive.first_text(["sos_commands/systemd/systemctl_list-timers_--all"])
    if timers:
        facts.evidence_paths.append(timers[0])
        facts.listed = "dnf-makecache.timer" in timers[1]
        if facts.active is None:
            facts.active = facts.listed
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
        if all_rsyslog or archive.read_text("etc/rsyslog.conf") is not None:
            facts.rsyslog_filter_present = False

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
                value = m.group(1).strip().strip("'\"")
                facts.cron_mailto = value
                break
    return facts
