from __future__ import annotations

import re
from collections.abc import Mapping

from sosdiag.model.facts import SelinuxFacts, SelinuxMode

_ERROR_MARKERS = (
    "command not found",
    "no such file or directory",
    "permission denied",
    "failed to",
    "not found",
)


def _is_usable(text: str | None) -> bool:
    if not text or not text.strip():
        return False
    lowered = text.lower()
    return not any(marker in lowered for marker in _ERROR_MARKERS)


def _normalize_mode(value: str | None) -> SelinuxMode | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    mapping: dict[str, SelinuxMode] = {
        "disabled": "Disabled",
        "permissive": "Permissive",
        "enforcing": "Enforcing",
    }
    return mapping.get(normalized)


def _parse_getenforce(text: str) -> SelinuxMode | None:
    return _normalize_mode(text.splitlines()[0] if text.splitlines() else None)


def _parse_sestatus(text: str) -> SelinuxMode | None:
    match = re.search(
        r"^SELinux status:\s*(enabled|disabled)\s*$",
        text,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    if match and match.group(1).lower() == "disabled":
        return "Disabled"

    match = re.search(
        r"^Current mode:\s*(enforcing|permissive)\s*$",
        text,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    return _normalize_mode(match.group(1) if match else None)


def _parse_config(text: str) -> SelinuxMode | None:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = re.match(r"SELINUX\s*=\s*['\"]?([^'\"#\s]+)", stripped, re.IGNORECASE)
        if match:
            return _normalize_mode(match.group(1))
    return None


def _parse_rhel_major(text: str | None) -> int | None:
    if not _is_usable(text):
        return None
    match = re.search(r"Red Hat Enterprise Linux(?: Server)?(?: release)?\s+(\d+)", text or "", re.IGNORECASE)
    if not match:
        match = re.search(r"VERSION_ID=['\"]?(\d+)", text or "", re.IGNORECASE)
    return int(match.group(1)) if match else None


def _parse_kernel_selinux_disabled(cmdline: str | None) -> bool | None:
    if not _is_usable(cmdline):
        return None
    return "selinux=0" in (cmdline or "").split()


def parse_selinux(sources: Mapping[str, str | None]) -> SelinuxFacts:
    rhel_major = _parse_rhel_major(sources.get("os_release"))

    runtime_mode: SelinuxMode | None = None
    runtime_source: str | None = None

    getenforce = sources.get("getenforce")
    if _is_usable(getenforce):
        runtime_mode = _parse_getenforce(getenforce or "")
        if runtime_mode is not None:
            runtime_source = "getenforce"

    if runtime_mode is None:
        sestatus = sources.get("sestatus")
        if _is_usable(sestatus):
            runtime_mode = _parse_sestatus(sestatus or "")
            if runtime_mode is not None:
                runtime_source = "sestatus"

    configured_mode: SelinuxMode | None = None
    configured_source: str | None = None
    config = sources.get("config")
    if _is_usable(config):
        configured_mode = _parse_config(config or "")
        if configured_mode is not None:
            configured_source = "/etc/selinux/config"

    mismatch: bool | None = None
    if runtime_mode is not None and configured_mode is not None:
        mismatch = runtime_mode != configured_mode

    kernel_cmdline = sources.get("cmdline") if _is_usable(sources.get("cmdline")) else None
    kernel_selinux_disabled = _parse_kernel_selinux_disabled(kernel_cmdline)

    return SelinuxFacts(
        rhel_major=rhel_major,
        runtime_mode=runtime_mode,
        configured_mode=configured_mode,
        runtime_config_mismatch=mismatch,
        runtime_source=runtime_source,
        configured_source=configured_source,
        kernel_cmdline=kernel_cmdline,
        kernel_selinux_disabled=kernel_selinux_disabled,
        kernel_cmdline_source="/proc/cmdline" if kernel_cmdline is not None else None,
    )
