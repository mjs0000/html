from __future__ import annotations

import re

from sosdiag.archive import SosArchive
from sosdiag.model.host import EvidenceRef, HostFacts


_RELEASE_RE = re.compile(r"release\s+(\d+)(?:\.(\d+))?", re.IGNORECASE)


def parse_host_facts(archive: SosArchive) -> HostFacts:
    facts = HostFacts()

    hostname = archive.first_text([
        "hostname",
        "etc/hostname",
        "sos_commands/host/hostname",
        "sos_commands/general/hostname",
    ])
    if hostname:
        path, text = hostname
        value = text.strip().splitlines()[0] if text.strip() else None
        if value:
            facts.hostname = value
            facts.evidence.append(EvidenceRef(path=path, value=value))

    release = archive.first_text(["etc/redhat-release", "etc/os-release"])
    if release:
        path, text = release
        facts.evidence.append(EvidenceRef(path=path, value=text.strip().splitlines()[0] if text.strip() else None))
        version = _parse_rhel_version(text)
        if version:
            facts.rhel_version, facts.rhel_major = version

    uname = archive.first_text([
        "sos_commands/kernel/uname_-a",
        "sos_commands/kernel/uname_-r",
        "uname",
    ])
    if uname:
        path, text = uname
        line = text.strip().splitlines()[0] if text.strip() else ""
        if line:
            facts.kernel_release = _kernel_release_from_uname(line)
            facts.architecture = _architecture_from_uname(line)
            facts.evidence.append(EvidenceRef(path=path, value=line))

    dmidecode = archive.first_text([
        "sos_commands/hardware/dmidecode",
        "sos_commands/hardware/dmidecode_--type_system",
    ])
    if dmidecode:
        path, text = dmidecode
        facts.manufacturer = _dmi_value(text, "Manufacturer")
        facts.product_name = _dmi_value(text, "Product Name")
        if facts.manufacturer or facts.product_name:
            facts.evidence.append(
                EvidenceRef(path=path, value=f"{facts.manufacturer or '-'} | {facts.product_name or '-'}")
            )

    virt = archive.first_text([
        "sos_commands/host/virt-what",
        "sos_commands/systemd/systemd-detect-virt",
        "sos_commands/host/systemd-detect-virt",
    ])
    if virt:
        path, text = virt
        value = text.strip().splitlines()[0] if text.strip() else None
        if value and value.lower() not in {"none", "no"}:
            facts.virtualization = value
            facts.host_type = "virtual"
            facts.evidence.append(EvidenceRef(path=path, value=value))

    if facts.host_type is None:
        dmi_hint = " ".join(filter(None, [facts.manufacturer, facts.product_name])).lower()
        if any(token in dmi_hint for token in ("vmware", "virtualbox", "kvm", "qemu", "microsoft corporation virtual")):
            facts.host_type = "virtual"
        elif facts.manufacturer or facts.product_name:
            facts.host_type = "physical"

    return facts


def _parse_rhel_version(text: str) -> tuple[str, int] | None:
    match = _RELEASE_RE.search(text)
    if match:
        version = match.group(1)
        if match.group(2):
            version += "." + match.group(2)
        return version, int(match.group(1))

    version_id = re.search(r'^VERSION_ID=["\']?([^"\'\n]+)', text, re.MULTILINE)
    if version_id:
        version = version_id.group(1).strip()
        major_text = version.split(".", 1)[0]
        if major_text.isdigit():
            return version, int(major_text)
    return None


def _kernel_release_from_uname(line: str) -> str | None:
    fields = line.split()
    if line.startswith("Linux ") and len(fields) >= 3:
        return fields[2]
    return fields[0] if fields else None


def _architecture_from_uname(line: str) -> str | None:
    fields = line.split()
    known = {"x86_64", "aarch64", "ppc64le", "s390x"}
    for field in reversed(fields):
        if field in known:
            return field
    return None


def _dmi_value(text: str, key: str) -> str | None:
    pattern = re.compile(rf"^\s*{re.escape(key)}:\s*(.+?)\s*$", re.MULTILINE)
    match = pattern.search(text)
    return match.group(1).strip() if match else None
