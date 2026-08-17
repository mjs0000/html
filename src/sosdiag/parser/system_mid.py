from __future__ import annotations

import re

from sosdiag.archive import SosArchive
from sosdiag.model.host import HostFacts
from sosdiag.model.system_mid import (
    CoreDumpFacts,
    DefaultServiceFacts,
    ErrorFinding,
    ErrorLogFacts,
    KernelParameterFacts,
    LogrotateSysstatFacts,
    ServiceState,
)

_DEFAULT_SERVICES = [
    "nis-domainname.service",
    "ostree-remount.service",
    "bluetooth.service",
    "cups.service",
    "atd.service",
    "wpa_supplicant.service",
    "avahi-daemon.service",
    "mdmonitor.service",
    "ModemManager.service",
    "rhsmcertd.service",
    "rtkit-daemon.service",
    "selinux-autorelabel-mark.service",
]

_KERNEL_PARAMS = [
    "vm.dirty_background_ratio",
    "vm.dirty_ratio",
    "vm.swappiness",
    "net.ipv4.ip_forward",
    "net.core.somaxconn",
    "net.ipv4.tcp_max_syn_backlog",
]


def parse_error_log_facts(archive: SosArchive) -> ErrorLogFacts:
    facts = ErrorLogFacts()
    candidates = [
        "var/log/messages",
        "sos_commands/kernel/dmesg",
        "sos_commands/logs/journalctl_--no-pager",
    ]
    signatures = [
        ("FAIL", "kernel panic", re.compile(r"kernel panic", re.I)),
        ("FAIL", "fatal oops/bug", re.compile(r"\b(?:oops|bug:)\b.*(?:fatal|panic)|general protection fault", re.I)),
        ("FAIL", "filesystem corruption", re.compile(r"(?:xfs.*metadata error|ext4-fs error|filesystem corruption)", re.I)),
        ("FAIL", "uncorrected hardware error", re.compile(r"(?:uncorrected|uncorrectable).*(?:mce|edac|hardware)", re.I)),
        ("WARN", "soft/hard lockup", re.compile(r"(?:soft|hard) lockup", re.I)),
        ("WARN", "hung task", re.compile(r"hung task|blocked for more than", re.I)),
        ("WARN", "watchdog", re.compile(r"watchdog", re.I)),
        ("WARN", "corrected hardware error", re.compile(r"corrected.*(?:mce|edac|hardware)", re.I)),
        ("WARN", "repeated reset/timeout", re.compile(r"(?:reset|timeout)", re.I)),
    ]
    seen: dict[tuple[str, str], ErrorFinding] = {}
    for candidate in candidates:
        text = archive.read_text(candidate)
        if not text or not text.strip():
            continue
        facts.usable_sources.append(candidate)
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            for severity, signature, pattern in signatures:
                if not pattern.search(stripped):
                    continue
                key = (severity, signature)
                if key not in seen:
                    seen[key] = ErrorFinding(source=candidate, severity=severity, signature=signature, message=stripped)
                else:
                    seen[key].count += 1
                break
    facts.findings = list(seen.values())
    return facts


def parse_kernel_parameter_facts(archive: SosArchive, host: HostFacts) -> KernelParameterFacts:
    facts = KernelParameterFacts(host_type=host.host_type)
    found = archive.first_text(["sos_commands/kernel/sysctl_-a"])
    if not found:
        return facts
    path, text = found
    facts.evidence_paths.append(path)
    for line in text.splitlines():
        if "=" not in line:
            continue
        name, value = [part.strip() for part in line.split("=", 1)]
        if name not in _KERNEL_PARAMS:
            continue
        try:
            facts.values[name] = int(value)
        except ValueError:
            facts.values[name] = value
    return facts


def parse_default_service_facts(archive: SosArchive) -> DefaultServiceFacts:
    facts = DefaultServiceFacts()
    unit_files = archive.first_text([
        "sos_commands/systemd/systemctl_list-unit-files",
        "sos_commands/systemd/systemctl_list-unit-files_--no-pager",
    ])
    units = archive.first_text([
        "sos_commands/systemd/systemctl_list-units",
        "sos_commands/systemd/systemctl_list-units_--all",
    ])
    unit_files_text = unit_files[1] if unit_files else ""
    units_text = units[1] if units else ""
    if unit_files:
        facts.evidence_paths.append(unit_files[0])
    if units:
        facts.evidence_paths.append(units[0])
    for service in _DEFAULT_SERVICES:
        state = ServiceState()
        m = re.search(rf"^{re.escape(service)}\s+(enabled|disabled|masked|static|indirect)\b", unit_files_text, re.M)
        if m:
            state.enabled = m.group(1) == "enabled"
        m = re.search(rf"^{re.escape(service)}\s+loaded\s+(active|inactive|failed)\b", units_text, re.M)
        if m:
            state.active = m.group(1) == "active"
        facts.services[service] = state
    return facts


def parse_coredump_facts(archive: SosArchive) -> CoreDumpFacts:
    facts = CoreDumpFacts()
    hard = archive.first_text(["sos_commands/process/ulimit_-aH"])
    soft = archive.first_text(["sos_commands/process/ulimit_-aS"])
    if hard:
        facts.evidence_paths.append(hard[0])
        facts.hard_core_limit = _extract_core_limit(hard[1])
    if soft:
        facts.evidence_paths.append(soft[0])
        facts.soft_core_limit = _extract_core_limit(soft[1])

    limits_texts = []
    for path in ["etc/security/limits.conf"]:
        text = archive.read_text(path)
        if text is not None:
            facts.evidence_paths.append(path)
            limits_texts.append(text)
    for path, text in archive.glob_text("etc/security/limits.d/*"):
        facts.evidence_paths.append(path)
        limits_texts.append(text)
    combined = "\n".join(limits_texts)
    if combined:
        facts.limits_soft_unlimited = bool(re.search(r"^\s*\*\s+soft\s+core\s+unlimited\b", combined, re.I | re.M))
        facts.limits_hard_unlimited = bool(re.search(r"^\s*\*\s+hard\s+core\s+unlimited\b", combined, re.I | re.M))

    system_conf = archive.read_text("etc/systemd/system.conf")
    if system_conf is not None:
        facts.evidence_paths.append("etc/systemd/system.conf")
        m = re.search(r"^\s*DefaultLimitCORE\s*=\s*([^#\s]+)", system_conf, re.I | re.M)
        facts.default_limit_core = m.group(1) if m else None

    local_tmpfiles = archive.glob_text("etc/tmpfiles.d/*")
    if local_tmpfiles:
        facts.evidence_paths.extend(path for path, _ in local_tmpfiles)
        facts.retention_override = any("/var/lib/systemd/coredump" in text and not re.search(r"\b3d\b", text) for _, text in local_tmpfiles)
    elif archive.read_text("usr/lib/tmpfiles.d/systemd.conf") is not None:
        facts.evidence_paths.append("usr/lib/tmpfiles.d/systemd.conf")
        facts.retention_override = False
    return facts


def parse_logrotate_sysstat_facts(archive: SosArchive) -> LogrotateSysstatFacts:
    facts = LogrotateSysstatFacts()
    conf = archive.read_text("etc/logrotate.conf")
    if conf is not None:
        facts.evidence_paths.append("etc/logrotate.conf")
        facts.logrotate_frequency = _first_directive(conf, ["daily", "weekly", "monthly", "yearly"])
        rotate = re.search(r"^\s*rotate\s+(\d+)\b", conf, re.M)
        if rotate:
            facts.logrotate_rotate_count = int(rotate.group(1))

    rpms = archive.first_text(["installed-rpms", "sos_commands/rpm/rpm_-qa"])
    if rpms:
        facts.evidence_paths.append(rpms[0])
        facts.sysstat_installed = bool(re.search(r"^sysstat(?:-|\s)", rpms[1], re.I | re.M))

    timer = archive.read_text("usr/lib/systemd/system/sysstat-collect.timer")
    overrides = archive.glob_text("etc/systemd/system/sysstat-collect.timer.d/*")
    timer_text = "\n".join([timer or "", *(text for _, text in overrides)])
    if timer is not None:
        facts.evidence_paths.append("usr/lib/systemd/system/sysstat-collect.timer")
    facts.evidence_paths.extend(path for path, _ in overrides)
    if timer_text:
        facts.sar_interval_minutes = _parse_oncalendar_interval(timer_text)

    wants = archive.read_text("etc/systemd/system/sysstat.service.wants/sysstat-collect.timer")
    list_timers = archive.first_text(["sos_commands/systemd/systemctl_list-timers_--all"])
    if wants is not None:
        facts.evidence_paths.append("etc/systemd/system/sysstat.service.wants/sysstat-collect.timer")
        facts.sysstat_enabled = True
    elif list_timers:
        facts.evidence_paths.append(list_timers[0])
        facts.sysstat_enabled = "sysstat-collect.timer" in list_timers[1]
    return facts


def _extract_core_limit(text: str) -> str | None:
    for line in text.splitlines():
        if "core file size" in line.lower() or re.search(r"\bcore\b", line, re.I):
            fields = line.split()
            if fields:
                return fields[-1]
    return None


def _first_directive(text: str, names: list[str]) -> str | None:
    for line in text.splitlines():
        stripped = line.strip().lower()
        if stripped in names:
            return stripped
    return None


def _parse_oncalendar_interval(text: str) -> int | None:
    m = re.search(r"OnCalendar\s*=\s*\*:00/(\d+)\b", text)
    if m:
        return int(m.group(1))
    return None
