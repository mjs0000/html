from __future__ import annotations

import re

from sosdiag.archive import SosArchive
from sosdiag.model.host import HostFacts
from sosdiag.model.system_runtime import ChronyFacts, FirewalldFacts, KdumpFacts, PackageUpdateFacts


def parse_package_update_facts(archive: SosArchive, host: HostFacts) -> PackageUpdateFacts:
    facts = PackageUpdateFacts(rhel_major=host.rhel_major, architecture=host.architecture, running_kernel=host.kernel_release)
    installed = archive.first_text(["installed-rpms", "sos_commands/rpm/rpm_-qa"])
    if installed:
        path, text = installed
        facts.evidence_paths.append(path)
        kernels = []
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("kernel-") or line.startswith("kernel "):
                kernels.append(line)
        facts.installed_kernels = sorted(set(kernels))
        if facts.installed_kernels:
            facts.newest_installed_kernel = facts.installed_kernels[-1]
    return facts


def parse_firewalld_facts(archive: SosArchive) -> FirewalldFacts:
    facts = FirewalldFacts()
    unit_files = archive.first_text(["sos_commands/systemd/systemctl_list-unit-files"])
    units = archive.first_text(["sos_commands/systemd/systemctl_list-units_--all", "sos_commands/systemd/systemctl_list-units"])
    if unit_files:
        path, text = unit_files
        facts.evidence_paths.append(path)
        facts.enabled = _unit_enabled(text, "firewalld.service")
    if units:
        path, text = units
        facts.evidence_paths.append(path)
        facts.active = _unit_active(text, "firewalld.service")
    zones = archive.first_text(["sos_commands/firewalld/firewall-cmd_--list-all-zones"])
    if zones:
        path, text = zones
        facts.evidence_paths.append(path)
        facts.zones_text = text.strip() or None
    return facts


def parse_chrony_facts(archive: SosArchive) -> ChronyFacts:
    facts = ChronyFacts()
    units = archive.first_text(["sos_commands/systemd/systemctl_list-units_--all", "sos_commands/systemd/systemctl_list-units"])
    if units:
        path, text = units
        facts.evidence_paths.append(path)
        facts.active = _unit_active(text, "chronyd.service")
    config = archive.first_text(["etc/chrony.conf"])
    if config:
        path, text = config
        facts.evidence_paths.append(path)
        count = 0
        for line in text.splitlines():
            line = line.strip()
            if line and not line.startswith("#") and line.split()[0] in {"server", "pool", "peer"}:
                count += 1
        facts.configured_source_count = count
    return facts


def parse_kdump_facts(archive: SosArchive) -> KdumpFacts:
    facts = KdumpFacts()
    unit_files = archive.first_text(["sos_commands/systemd/systemctl_list-unit-files"])
    units = archive.first_text(["sos_commands/systemd/systemctl_list-units_--all", "sos_commands/systemd/systemctl_list-units"])
    if unit_files:
        path, text = unit_files
        facts.evidence_paths.append(path)
        facts.enabled = _unit_enabled(text, "kdump.service")
    if units:
        path, text = units
        facts.evidence_paths.append(path)
        facts.active = _unit_active(text, "kdump.service")
    cmdline = archive.first_text(["proc/cmdline"])
    if cmdline:
        path, text = cmdline
        facts.evidence_paths.append(path)
        match = re.search(r"crashkernel=([^ ]+)", text)
        if match:
            facts.crashkernel_parameter = match.group(1)
    crash_size = archive.first_text(["sys/kernel/kexec_crash_size"])
    if crash_size:
        path, text = crash_size
        facts.evidence_paths.append(path)
        try:
            facts.kexec_crash_size = int(text.strip())
        except ValueError:
            pass
    showmem = archive.first_text(["sos_commands/kdump/kdumpctl_showmem"])
    if showmem:
        path, text = showmem
        facts.evidence_paths.append(path)
        facts.kdumpctl_showmem = text.strip() or None
    sysctl = archive.first_text(["sos_commands/kernel/sysctl_-a"])
    if sysctl:
        path, text = sysctl
        facts.evidence_paths.append(path)
        wanted = {"kernel.nmi_watchdog", "kernel.panic_on_io_nmi", "kernel.panic_on_unrecovered_nmi", "kernel.unknown_nmi_panic", "kernel.sysrq", "kernel.hung_task_panic", "kernel.panic_on_oops", "kernel.panic", "kernel.softlockup_panic"}
        for line in text.splitlines():
            if "=" not in line:
                continue
            name, value = [part.strip() for part in line.split("=", 1)]
            if name not in wanted:
                continue
            try:
                facts.parameters[name] = int(value)
            except ValueError:
                facts.parameters[name] = value
    return facts


def _unit_enabled(text: str, unit: str) -> bool | None:
    for line in text.splitlines():
        fields = line.split()
        if fields and fields[0] == unit and len(fields) > 1:
            return fields[1] == "enabled"
    return None


def _unit_active(text: str, unit: str) -> bool | None:
    for line in text.splitlines():
        if unit not in line:
            continue
        lower = line.lower()
        if " active " in f" {lower} " and (" running " in f" {lower} " or " exited " in f" {lower} "):
            return True
        if " inactive " in f" {lower} " or " failed " in f" {lower} ":
            return False
    return None
