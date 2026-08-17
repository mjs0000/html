from __future__ import annotations

import re
from dataclasses import dataclass

from sosdiag.archive import SosArchive


@dataclass(frozen=True)
class SystemdUnitState:
    enabled: bool | None
    active: bool | None
    enablement_state: str | None
    active_state: str | None
    evidence_paths: tuple[str, ...]


def parse_systemd_unit_state(archive: SosArchive, unit: str) -> SystemdUnitState:
    paths: list[str] = []
    enablement_state: str | None = None
    active_state: str | None = None

    unit_files = archive.first_text([
        "sos_commands/systemd/systemctl_list-unit-files",
        "sos_commands/systemd/systemctl_list-unit-files_--no-pager",
        "sos_commands/systemd/systemctl_list-unit-files_--all",
    ])
    units = archive.first_text([
        "sos_commands/systemd/systemctl_list-units_--all",
        "sos_commands/systemd/systemctl_list-units",
    ])

    if unit_files:
        paths.append(unit_files[0])
        for line in unit_files[1].splitlines():
            fields = line.split()
            if not fields or fields[0] != unit or len(fields) < 2:
                continue
            enablement_state = fields[1].strip().lower()
            break

    if units:
        paths.append(units[0])
        pattern = re.compile(rf"^\s*[●*]?\s*{re.escape(unit)}\s+\S+\s+(\S+)\s+(\S+)\b", re.I)
        for line in units[1].splitlines():
            match = pattern.search(line)
            if not match:
                continue
            # systemctl list-units columns are UNIT LOAD ACTIVE SUB DESCRIPTION.
            active_state = match.group(1).strip().lower()
            break

    enabled: bool | None
    if enablement_state in {"enabled", "enabled-runtime"}:
        enabled = True
    elif enablement_state in {"disabled", "masked", "masked-runtime"}:
        enabled = False
    else:
        # static/indirect/generated/alias/linked/transient are not equivalent to disabled.
        enabled = None

    active: bool | None
    if active_state == "active":
        active = True
    elif active_state in {"inactive", "failed"}:
        active = False
    else:
        active = None

    return SystemdUnitState(
        enabled=enabled,
        active=active,
        enablement_state=enablement_state,
        active_state=active_state,
        evidence_paths=tuple(dict.fromkeys(paths)),
    )
