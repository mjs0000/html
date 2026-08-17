from __future__ import annotations

import re

from sosdiag.archive import SosArchive
from sosdiag.model.network_storage import (
    BondFacts,
    BondSlave,
    BondingFacts,
    MultipathFacts,
    MultipathMap,
    MultipathPath,
    NetstateFacts,
    NetworkInterfaceFacts,
    NetworkKernelFacts,
)

_NET_SYSCTLS = {
    "net.core.netdev_max_backlog",
    "net.ipv4.tcp_rmem",
    "net.ipv4.tcp_wmem",
    "net.core.rmem_max",
    "net.core.wmem_max",
    "vm.min_free_kbytes",
    "net.core.netdev_budget",
}


def parse_bonding_facts(archive: SosArchive) -> BondingFacts:
    facts = BondingFacts()
    candidates = archive.glob_text("proc/net/bonding/*") + archive.glob_text("proc/*/net/bonding/*")
    seen_bonds: set[str] = set()
    for path, text in candidates:
        bond_name = path.rsplit("/", 1)[-1]
        if bond_name in seen_bonds:
            continue
        seen_bonds.add(bond_name)
        bond = BondFacts(bond_name=bond_name, evidence_path=path)
        m = re.search(r"^Bonding Mode:\s*(.+)$", text, re.M)
        if m:
            bond.mode = m.group(1).strip().lower()
        m = re.search(r"^MII Status:\s*(\S+)", text, re.M)
        if m:
            bond.mii_status = m.group(1).strip().lower()
        m = re.search(r"^MII Polling Interval \(ms\):\s*(\d+)", text, re.M)
        if m:
            bond.miimon = int(m.group(1))
        m = re.search(r"^Currently Active Slave:\s*(.+)$", text, re.M)
        if m:
            bond.active_slave = m.group(1).strip()
        m = re.search(r"^LACP rate:\s*(.+)$", text, re.M | re.I)
        if m:
            bond.lacp_rate = m.group(1).strip()

        chunks = re.split(r"^Slave Interface:\s*", text, flags=re.M)[1:]
        for chunk in chunks:
            lines = chunk.splitlines()
            name = lines[0].strip() if lines else ""
            state_match = re.search(r"^MII Status:\s*(\S+)", chunk, re.M)
            if name:
                bond.slaves.append(BondSlave(name=name, link_state=state_match.group(1).lower() if state_match else None))
        facts.bonds.append(bond)
    return facts


def parse_network_kernel_facts(archive: SosArchive) -> NetworkKernelFacts:
    facts = NetworkKernelFacts()
    nmcli_dev = archive.first_text([
        "sos_commands/networkmanager/nmcli_dev",
        "sos_commands/networkmanager/nmcli_device",
    ])
    active = archive.first_text([
        "sos_commands/networkmanager/nmcli_con_--active",
        "sos_commands/networkmanager/nmcli_con_show_--active",
    ])

    device_rows = _parse_nmcli_device_rows(nmcli_dev[1]) if nmcli_dev else {}
    active_rows = _parse_nmcli_active_rows(active[1]) if active else {}
    configured_ip = _configured_ip_interfaces(archive)
    link_rows = _parse_ip_link_rows(archive)
    if nmcli_dev:
        facts.evidence_paths.append(nmcli_dev[0])
    if active:
        facts.evidence_paths.append(active[0])

    for path, iface, text in _direct_ethtool_entries(archive):
        speed = _parse_speed(text)
        link_up = _parse_link(text)
        if speed is None or speed < 10000 or link_up is not True:
            continue
        if not _is_active_physical_ethernet(iface, device_rows, active_rows, configured_ip, link_rows):
            continue
        facts.qualifying_interface = iface
        facts.speed_mbps = speed
        facts.link_up = True
        facts.configured = True
        facts.evidence_paths.append(path)
        break

    sysctl = archive.first_text(["sos_commands/kernel/sysctl_-a"])
    if sysctl:
        facts.evidence_paths.append(sysctl[0])
        for line in sysctl[1].splitlines():
            if "=" not in line:
                continue
            name, raw = [x.strip() for x in line.split("=", 1)]
            if name not in _NET_SYSCTLS:
                continue
            if name in {"net.ipv4.tcp_rmem", "net.ipv4.tcp_wmem"}:
                try:
                    facts.values[name] = [int(x) for x in raw.split()]
                except ValueError:
                    facts.values[name] = raw
            else:
                try:
                    facts.values[name] = int(raw)
                except ValueError:
                    facts.values[name] = raw
    facts.evidence_paths = list(dict.fromkeys(facts.evidence_paths))
    return facts


def parse_netstate_facts(archive: SosArchive) -> NetstateFacts:
    facts = NetstateFacts()
    unit_files = archive.first_text(["sos_commands/systemd/systemctl_list-unit-files"])
    units = archive.first_text(["sos_commands/systemd/systemctl_list-units", "sos_commands/systemd/systemctl_list-units_--all"])
    if unit_files:
        facts.evidence_paths.append(unit_files[0])
        m = re.search(r"^NetworkManager\.service\s+(enabled|disabled|masked|static)\b", unit_files[1], re.M)
        if m:
            facts.networkmanager_enabled = m.group(1) == "enabled"
    if units:
        facts.evidence_paths.append(units[0])
        m = re.search(r"^NetworkManager\.service\s+loaded\s+(active|inactive|failed)\b", units[1], re.M)
        if m:
            facts.networkmanager_active = m.group(1) == "active"

    nmcli_dev = archive.first_text(["sos_commands/networkmanager/nmcli_dev", "sos_commands/networkmanager/nmcli_device"])
    active = archive.first_text(["sos_commands/networkmanager/nmcli_con_--active", "sos_commands/networkmanager/nmcli_con_show_--active"])
    if nmcli_dev or active:
        facts.nmcli_evidence_available = True
        facts.networkmanager_in_use = True
    elif facts.networkmanager_active is False:
        facts.networkmanager_in_use = False

    link_rows = _parse_ip_link_rows(archive)
    configured_ip = _configured_ip_interfaces(archive)

    if nmcli_dev:
        facts.evidence_paths.append(nmcli_dev[0])
        for iface, (connection_type, state) in _parse_nmcli_device_rows(nmcli_dev[1]).items():
            if iface == "lo":
                continue
            excluded = _is_non_reportable_virtual_iface(iface, connection_type)
            connected = state in {"connected", "connecting"} and not excluded
            facts.interfaces.append(NetworkInterfaceFacts(
                interface_name=iface,
                connection_type=connection_type,
                master_interface=link_rows.get(iface, {}).get("master"),
                configured=connected,
                active_connection=state == "connected" and not excluded,
                carrier=True if state == "connected" and not excluded else None,
                operational_state=state,
            ))
    else:
        for iface in sorted(configured_ip):
            if iface == "lo" or _is_non_reportable_virtual_iface(iface, None):
                continue
            link = link_rows.get(iface, {})
            is_up = link.get("up")
            facts.interfaces.append(NetworkInterfaceFacts(
                interface_name=iface,
                master_interface=link.get("master"),
                configured=True,
                active_connection=True,
                carrier=is_up,
                operational_state=link.get("state"),
            ))

    known = {i.interface_name for i in facts.interfaces}
    for path, iface, text in _direct_ethtool_entries(archive):
        if iface == "lo":
            continue
        speed = _parse_speed(text)
        link = _parse_link(text)
        match = next((i for i in facts.interfaces if i.interface_name == iface), None)
        if match:
            match.speed_mbps = speed
            if link is not None:
                match.carrier = link
        elif iface not in known and not _is_non_reportable_virtual_iface(iface, None):
            facts.interfaces.append(NetworkInterfaceFacts(interface_name=iface, carrier=link, speed_mbps=speed))
            known.add(iface)
        facts.evidence_paths.append(path)
    facts.evidence_paths = list(dict.fromkeys(facts.evidence_paths))
    return facts


def parse_multipath_facts(archive: SosArchive) -> MultipathFacts:
    facts = MultipathFacts()
    found = archive.first_text(["sos_commands/multipath/multipath_-ll", "sos_commands/multipath/multipath_ll"])
    if not found:
        return facts
    path, text = found
    facts.evidence_paths.append(path)
    current: MultipathMap | None = None
    group_index = 0
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        header = re.match(r"^(\S+)\s+\(([^)]+)\)\s+dm-\d+\s+([^,]+),(.+)$", line)
        if header:
            current = MultipathMap(map_name=header.group(1), wwid=header.group(2), vendor=header.group(3).strip(), product=header.group(4).strip())
            facts.maps.append(current)
            group_index = 0
            continue
        if current is None:
            continue
        if "policy=" in line or "prio=" in line:
            group_index += 1
            continue
        pm = re.search(r"(\d+:\d+:\d+:\d+)\s+(\S+)\s+\d+:\d+\s+(\S+)\s+(\S+)\s+(\S+)", line)
        if pm:
            current.paths.append(MultipathPath(
                hctl=pm.group(1),
                device=pm.group(2),
                path_state=pm.group(3).lower(),
                dm_state=pm.group(4).lower(),
                path_group=str(group_index) if group_index else None,
            ))
    conf = archive.first_text(["sos_commands/multipath/multipathd_show_config"])
    if conf:
        facts.effective_config_available = bool(conf[1].strip())
        facts.evidence_paths.append(conf[0])
    elif archive.read_text("etc/multipath.conf") is not None:
        facts.effective_config_available = True
        facts.evidence_paths.append("etc/multipath.conf")
    return facts


def _parse_nmcli_device_rows(text: str) -> dict[str, tuple[str | None, str | None]]:
    rows: dict[str, tuple[str | None, str | None]] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.upper().startswith("DEVICE "):
            continue
        fields = stripped.split()
        if len(fields) < 3:
            continue
        rows[fields[0]] = (fields[1].lower(), fields[2].lower())
    return rows


def _parse_nmcli_active_rows(text: str) -> dict[str, str | None]:
    rows: dict[str, str | None] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.upper().startswith("NAME "):
            continue
        fields = stripped.split()
        if len(fields) < 4:
            continue
        device = fields[-1]
        connection_type = fields[-2].lower()
        if device and device != "--":
            rows[device] = connection_type
    return rows


def _configured_ip_interfaces(archive: SosArchive) -> set[str]:
    configured: set[str] = set()
    addr = archive.first_text(["sos_commands/networking/ip_-o_addr"])
    if addr:
        for line in addr[1].splitlines():
            m = re.match(r"^\d+:\s+([^\s:]+)(?::\S+)?\s+inet6?\s+(\S+)\s+", line)
            if not m:
                continue
            iface, address = m.group(1), m.group(2)
            if iface != "lo" and not address.lower().startswith("fe80:"):
                configured.add(iface)
    routes = archive.first_text(["sos_commands/networking/ip_route_show_table_all"])
    if routes:
        for line in routes[1].splitlines():
            if " linkdown " in f" {line} ":
                continue
            m = re.search(r"\bdev\s+(\S+)", line)
            if m and m.group(1) != "lo":
                configured.add(m.group(1))
    return configured


def _parse_ip_link_rows(archive: SosArchive) -> dict[str, dict[str, object]]:
    found = archive.first_text(["sos_commands/networking/ip_-s_-d_link"])
    if not found:
        return {}
    rows: dict[str, dict[str, object]] = {}
    current: str | None = None
    for line in found[1].splitlines():
        m = re.match(r"^\d+:\s+([^:@]+)(?:@[^:]+)?:\s+<([^>]*)>.*?\bstate\s+(\S+)", line)
        if m:
            current = m.group(1)
            flags = {part.strip().upper() for part in m.group(2).split(",")}
            master = None
            mm = re.search(r"\bmaster\s+(\S+)", line)
            if mm:
                master = mm.group(1)
            rows[current] = {
                "flags": flags,
                "state": m.group(3).upper(),
                "master": master,
                "physical": False,
                "up": "UP" in flags and "LOWER_UP" in flags,
            }
            continue
        if current and current in rows:
            if "parentbus pci" in line.lower() or re.search(r"\bparentdev\s+[0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-9a-f]\b", line, re.I):
                rows[current]["physical"] = True
    return rows


def _is_non_reportable_virtual_iface(iface: str, connection_type: str | None) -> bool:
    lower = iface.lower()
    if connection_type in {"bridge", "tun", "tap", "vxlan", "dummy", "loopback"}:
        return True
    return lower.startswith(("virbr", "veth", "docker", "cni", "podman", "tap", "tun", "vxlan"))


def _is_active_physical_ethernet(
    iface: str,
    device_rows: dict[str, tuple[str | None, str | None]],
    active_rows: dict[str, str | None],
    configured_ip: set[str],
    link_rows: dict[str, dict[str, object]],
) -> bool:
    device_type: str | None = None
    device_state: str | None = None
    if iface in device_rows:
        device_type, device_state = device_rows[iface]
    active_type = active_rows.get(iface)

    nmcli_ok = iface in active_rows
    if nmcli_ok:
        if device_type is not None and device_type != "ethernet":
            nmcli_ok = False
        if active_type is not None and active_type != "ethernet":
            nmcli_ok = False
        if device_type is None and active_type is None:
            nmcli_ok = False
        if device_state is not None and device_state not in {"connected", "connecting"}:
            nmcli_ok = False

    link = link_rows.get(iface, {})
    ip_ok = bool(
        iface in configured_ip
        and link.get("physical") is True
        and link.get("up") is True
    )
    return nmcli_ok or ip_ok


def _direct_ethtool_entries(archive: SosArchive) -> list[tuple[str, str, str]]:
    entries: list[tuple[str, str, str]] = []
    for path, text in archive.glob_text("sos_commands/networking/ethtool_*"):
        suffix = path.split("ethtool_", 1)[-1]
        if not suffix or suffix.startswith("-"):
            continue
        entries.append((path, suffix, text))
    return entries


def _parse_speed(text: str) -> int | None:
    m = re.search(r"Speed:\s*(\d+)Mb/s", text, re.I)
    return int(m.group(1)) if m else None


def _parse_link(text: str) -> bool | None:
    m = re.search(r"Link detected:\s*(yes|no)", text, re.I)
    if not m:
        return None
    return m.group(1).lower() == "yes"
