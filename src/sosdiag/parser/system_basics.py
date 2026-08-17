from __future__ import annotations

import re

from sosdiag.archive import SosArchive
from sosdiag.model.host import HostFacts
from sosdiag.model.system_basics import (
    BootModeFacts,
    FilesystemEntry,
    FilesystemFacts,
    HardwareCertificationFacts,
    LifecycleFacts,
)


def parse_hardware_certification_facts(host: HostFacts) -> HardwareCertificationFacts:
    return HardwareCertificationFacts(
        host_type=host.host_type,
        manufacturer=host.manufacturer,
        product_name=host.product_name,
        rhel_version=host.rhel_version,
        virtualization=host.virtualization,
        evidence_paths=[item.path for item in host.evidence],
    )


def parse_lifecycle_facts(host: HostFacts) -> LifecycleFacts:
    return LifecycleFacts(
        rhel_version=host.rhel_version,
        rhel_major=host.rhel_major,
        evidence_paths=[item.path for item in host.evidence if item.path in {"etc/redhat-release", "etc/os-release"}],
    )


def parse_boot_mode_facts(archive: SosArchive) -> BootModeFacts:
    facts = BootModeFacts()
    paths = archive.paths()

    if any(path == "sys/firmware/efi" or path.startswith("sys/firmware/efi/") for path in paths):
        facts.direct_efi_present = True
        facts.mode = "UEFI"
        facts.evidence_paths.append("sys/firmware/efi")
        return facts

    firmware_listing = archive.first_text([
        "sos_commands/boot/ls_-alZR_.sys.firmware",
        "sos_commands/boot/ls_-lanR_.sys.firmware",
    ])
    if firmware_listing:
        path, text = firmware_listing
        facts.evidence_paths.append(path)
        if re.search(r"(?:^|\n)/sys/firmware/efi:\s*(?:\n|$)", text):
            facts.firmware_listing_has_efi = True
            facts.mode = "UEFI"
            return facts
        facts.firmware_listing_has_efi = False

    efibootmgr = archive.first_text([
        "sos_commands/boot/efibootmgr_-v",
        "sos_commands/boot/efibootmgr",
    ])
    if efibootmgr:
        path, text = efibootmgr
        facts.evidence_paths.append(path)
        facts.efibootmgr_available = bool(text.strip())
        if facts.efibootmgr_available and "EFI variables are not supported" not in text:
            facts.mode = "UEFI"
            return facts

    # If we have explicit firmware inventory but no EFI directory, treat this as BIOS.
    if firmware_listing and facts.firmware_listing_has_efi is False:
        facts.mode = "BIOS"
    return facts


def parse_filesystem_facts(archive: SosArchive) -> FilesystemFacts:
    facts = FilesystemFacts()
    findmnt = archive.first_text([
        "sos_commands/filesys/findmnt",
        "sos_commands/filesys/findmnt_-rno_TARGET,SOURCE,FSTYPE",
    ])
    lsblk = archive.first_text([
        "sos_commands/block/lsblk_-f_-a_-l",
        "sos_commands/block/lsblk_-f",
    ])

    if findmnt:
        path, text = findmnt
        facts.evidence_paths.append(path)
        entries = _parse_findmnt(text)
        facts.entries.extend(entries)

    if lsblk:
        path, text = lsblk
        facts.evidence_paths.append(path)
        lvm_devices = _parse_lvm_devices_from_lsblk(text)
        for entry in facts.entries:
            if entry.device:
                entry.lvm = _looks_like_lvm(entry.device, lvm_devices)

    for path, _ in archive.glob_text("sos_commands/lvm2/*"):
        if path not in facts.evidence_paths:
            facts.evidence_paths.append(path)

    return facts


def _parse_findmnt(text: str) -> list[FilesystemEntry]:
    entries: list[FilesystemEntry] = []
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("TARGET") or stripped.startswith("├") or stripped.startswith("└"):
            continue
        # Common sosreport findmnt output: TARGET SOURCE FSTYPE OPTIONS...
        parts = stripped.replace("├─", "").replace("└─", "").split()
        if len(parts) < 3:
            continue
        target, source, fstype = parts[0], parts[1], parts[2]
        if not target.startswith("/"):
            continue
        entries.append(FilesystemEntry(mount_point=target, device=source, filesystem_type=fstype))
    return entries


def _parse_lvm_devices_from_lsblk(text: str) -> set[str]:
    devices: set[str] = set()
    for line in text.splitlines():
        if " lvm " in f" {line.lower()} " or "LVM2_member" in line:
            fields = line.replace("├─", "").replace("└─", "").split()
            if fields:
                name = fields[0]
                devices.add(name)
                devices.add("/dev/" + name)
    return devices


def _looks_like_lvm(device: str, lvm_devices: set[str]) -> bool:
    if device.startswith("/dev/mapper/") or re.match(r"^/dev/[^/]+/[^/]+$", device):
        return True
    base = device.rsplit("/", 1)[-1]
    return device in lvm_devices or base in lvm_devices
