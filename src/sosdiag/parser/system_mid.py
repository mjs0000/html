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
from sosdiag.parser.systemd import parse_systemd_unit_state

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

_FATAL_SIGNATURES = [
    ("kernel panic", re.compile(r"kernel panic", re.I), "kernel"),
    ("fatal oops/bug", re.compile(r"(?:\boops\b|\bBUG:) .*?(?:fatal|panic)|general protection fault", re.I), "kernel"),
    ("filesystem corruption", re.compile(r"(?:xfs.*metadata error|ext4-fs error|filesystem corruption)", re.I), "filesystem"),
    ("uncorrected hardware error", re.compile(r"(?:uncorrected|uncorrectable).*(?:mce|edac|hardware|machine check)", re.I), "hardware"),
]

_WARN_SIGNATURES = [
    ("soft/hard lockup", re.compile(r"(?:soft|hard) lockup", re.I), "kernel"),
    ("hung task", re.compile(r"hung task|blocked for more than", re.I), "kernel"),
    ("watchdog", re.compile(r"watchdog.*(?:lockup|stuck|hard|soft|BUG|failure)", re.I), "kernel"),
    ("corrected hardware error", re.compile(r"corrected.*(?:mce|edac|hardware|machine check)", re.I), "hardware"),
]

_REPEAT_SIGNATURES = [
    ("repeated reset", re.compile(r"\breset(?:ting|ted)?\b", re.I), "device"),
    ("repeated timeout", re.compile(r"\btime(?:d)?\s*out\b|\btimeout\b", re.I), "device"),
]

_LOGROTATE_FREQS = {"daily", "weekly", "monthly", "yearly"}


def parse_error_log_facts(archive: SosArchive) -> ErrorLogFacts:
    facts = ErrorLogFacts()
    candidates = [
        "var/log/messages",
        "sos_commands/kernel/dmesg",
        "sos_commands/logs/journalctl_--no-pager",
    ]
    direct: dict[tuple[str, str, str], ErrorFinding] = {}
    repeated: dict[tuple[str, str], list[tuple[str, str]]] = {}

    for candidate in candidates:
        text = archive.read_text(candidate)
        if not text or not text.strip():
            continue
        facts.usable_sources.append(candidate)
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue

            matched = False
            for signature, pattern, impact in _FATAL_SIGNATURES:
                if pattern.search(stripped):
                    _record_error(direct, candidate, "FAIL", signature, stripped, impact)
                    matched = True
                    break
            if matched:
                continue

            for signature, pattern, impact in _WARN_SIGNATURES:
                if pattern.search(stripped):
                    _record_error(direct, candidate, "WARN", signature, stripped, impact)
                    matched = True
                    break
            if matched:
                continue

            for signature, pattern, impact in _REPEAT_SIGNATURES:
                if pattern.search(stripped):
                    key = (signature, _normalize_log_signature(stripped))
                    repeated.setdefault(key, []).append((candidate, stripped))
                    break

    for (signature, _), occurrences in repeated.items():
        if len(occurrences) < 3:
            continue
        source, message = occurrences[0]
        first_ts = _extract_log_timestamp(occurrences[0][1])
        last_ts = _extract_log_timestamp(occurrences[-1][1])
        finding = ErrorFinding(
            source=source,
            severity="WARN",
            signature=signature,
            message=message,
            count=len(occurrences),
            timestamp=first_ts,
            first_seen=first_ts,
            last_seen=last_ts,
            component=_infer_component(message),
            impact_category="device",
        )
        direct[(finding.severity, finding.signature, _normalize_log_signature(message))] = finding

    facts.findings = list(direct.values())
    return facts


def _record_error(
    target: dict[tuple[str, str, str], ErrorFinding],
    source: str,
    severity: str,
    signature: str,
    message: str,
    impact: str,
) -> None:
    normalized = _normalize_log_signature(message)
    key = (severity, signature, normalized)
    timestamp = _extract_log_timestamp(message)
    if key not in target:
        target[key] = ErrorFinding(
            source=source,
            severity=severity,
            signature=signature,
            message=message,
            timestamp=timestamp,
            first_seen=timestamp,
            last_seen=timestamp,
            component=_infer_component(message),
            impact_category=impact,
        )
    else:
        target[key].count += 1
        if timestamp:
            target[key].last_seen = timestamp


def _extract_log_timestamp(line: str) -> str | None:
    patterns = [
        r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[+-]\d{2}:?\d{2}|Z)?)",
        r"^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})",
        r"^([A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})",
        r"^\[\s*([0-9]+(?:\.[0-9]+)?)\]",
    ]
    for pattern in patterns:
        match = re.search(pattern, line)
        if match:
            return match.group(1)
    return None


def _normalize_log_signature(line: str) -> str:
    value = line.lower()
    value = re.sub(r"0x[0-9a-f]+", "<hex>", value)
    value = re.sub(r"\b\d+(?:\.\d+){1,3}\b", "<num>", value)
    value = re.sub(r"\b\d+\b", "<num>", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _infer_component(line: str) -> str | None:
    match = re.search(r"\b([A-Za-z0-9_.-]+)(?:\[\d+\])?:\s", line)
    return match.group(1) if match else None


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
    for service in _DEFAULT_SERVICES:
        parsed = parse_systemd_unit_state(archive, service)
        facts.services[service] = ServiceState(enabled=parsed.enabled, active=parsed.active)
        facts.evidence_paths.extend(parsed.evidence_paths)
    facts.evidence_paths = list(dict.fromkeys(facts.evidence_paths))
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
        facts.retention_override = any(_prevents_coredump_cleanup(text) for _, text in local_tmpfiles)
    else:
        vendor_tmpfiles = archive.read_text("usr/lib/tmpfiles.d/systemd.conf")
        if vendor_tmpfiles is not None:
            facts.evidence_paths.append("usr/lib/tmpfiles.d/systemd.conf")
            if "/var/lib/systemd/coredump" in vendor_tmpfiles:
                facts.retention_override = False

    facts.evidence_paths = list(dict.fromkeys(facts.evidence_paths))
    return facts


def _prevents_coredump_cleanup(text: str) -> bool:
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        fields = stripped.split()
        if len(fields) < 2 or fields[1] != "/var/lib/systemd/coredump":
            continue
        directive = fields[0]
        if directive in {"x", "X"}:
            return True
        if directive in {"d", "D"} and len(fields) >= 6 and fields[5] == "-":
            return True
    return False


def parse_logrotate_sysstat_facts(archive: SosArchive) -> LogrotateSysstatFacts:
    facts = LogrotateSysstatFacts()

    config_entries: list[tuple[str, str]] = []
    conf = archive.read_text("etc/logrotate.conf")
    if conf is not None:
        config_entries.append(("etc/logrotate.conf", conf))
    config_entries.extend(archive.glob_text("etc/logrotate.d/*"))

    frequencies: list[str] = []
    rotate_counts: list[int] = []
    for path, text in config_entries:
        facts.evidence_paths.append(path)
        frequencies.extend(_all_logrotate_frequencies(text))
        rotate_counts.extend(_all_logrotate_rotate_counts(text))

    debug_entries = archive.glob_text("sos_commands/logrotate/logrotate_-d_*")
    debug_freqs: list[str] = []
    debug_counts: list[int] = []
    for path, text in debug_entries:
        facts.evidence_paths.append(path)
        debug_freqs.extend(_all_logrotate_frequencies(text))
        debug_counts.extend(_all_logrotate_rotate_counts(text))

    if debug_freqs or debug_counts:
        facts.logrotate_effective_source = "logrotate_debug"
        frequencies = debug_freqs or frequencies
        rotate_counts = debug_counts or rotate_counts
    elif config_entries:
        facts.logrotate_effective_source = "config"

    facts.logrotate_frequencies = list(dict.fromkeys(frequencies))
    facts.logrotate_rotate_counts = list(dict.fromkeys(rotate_counts))
    if len(facts.logrotate_frequencies) == 1:
        facts.logrotate_frequency = facts.logrotate_frequencies[0]
    if len(facts.logrotate_rotate_counts) == 1:
        facts.logrotate_rotate_count = facts.logrotate_rotate_counts[0]

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

    timer_state = parse_systemd_unit_state(archive, "sysstat-collect.timer")
    facts.evidence_paths.extend(timer_state.evidence_paths)
    if timer_state.enabled is not None:
        facts.sysstat_enabled = timer_state.enabled
    else:
        wants = archive.read_text("etc/systemd/system/sysstat.service.wants/sysstat-collect.timer")
        list_timers = archive.first_text(["sos_commands/systemd/systemctl_list-timers_--all"])
        if wants is not None:
            facts.evidence_paths.append("etc/systemd/system/sysstat.service.wants/sysstat-collect.timer")
            facts.sysstat_enabled = True
        elif list_timers:
            facts.evidence_paths.append(list_timers[0])
            facts.sysstat_enabled = "sysstat-collect.timer" in list_timers[1]

    facts.evidence_paths = list(dict.fromkeys(facts.evidence_paths))
    return facts


def _extract_core_limit(text: str) -> str | None:
    for line in text.splitlines():
        if "core file size" in line.lower() or re.search(r"\bcore\b", line, re.I):
            fields = line.split()
            if fields:
                return fields[-1]
    return None


def _all_logrotate_frequencies(text: str) -> list[str]:
    values: list[str] = []
    for raw in text.splitlines():
        stripped = raw.strip().lower()
        if not stripped or stripped.startswith("#"):
            continue
        token = stripped.split()[0]
        if token in _LOGROTATE_FREQS:
            values.append(token)
    return values


def _all_logrotate_rotate_counts(text: str) -> list[int]:
    values: list[int] = []
    for match in re.finditer(r"^\s*rotate\s+(\d+)\b", text, re.I | re.M):
        values.append(int(match.group(1)))
    return values


def _parse_oncalendar_interval(text: str) -> int | None:
    values = []
    for match in re.finditer(r"^\s*OnCalendar\s*=\s*([^#\n]*)", text, re.I | re.M):
        value = match.group(1).strip()
        if not value:
            values.clear()
            continue
        values.append(value)
    for value in reversed(values):
        match = re.search(r"\*:00/(\d+)\b", value)
        if match:
            return int(match.group(1))
        if value.lower() in {"minutely", "*-*-* *:*:00"}:
            return 1
    return None
