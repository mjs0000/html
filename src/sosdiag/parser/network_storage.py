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
    for path, text in archive.glob_text("proc/net/bonding/*"):
        bond_name = path.rsplit("/", 1)[-1]
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
    active = archive.first_text([
        "sos_commands/networkmanager/nmcli_con_--active",
        "sos_commands/networkmanager/nmcli_con_show_--active",
        "sos_commands/networkmanager/nmcli_con",
    ])
    active_text = active[1] if active else ""
    if active:
        facts.evidence_paths.append(active[0])

    for path, text in archive.glob_text("sos_commands/networking/ethtool_*"):
        speed = _parse_speed(text)
        link_up = _parse_link(text)
        if speed is None or speed < 10000 or link_up is not True:
            continue
        iface = path.split("ethtool_", 1)[-1]
        configured = bool(re.search(rf"\b{re.escape(iface)}\b", active_text)) if active_text else None
        if configured is True:
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

    if nmcli_dev:
        facts.evidence_paths.append(nmcli_dev[0])
        for line in nmcli_dev[1].splitlines():
            if not line.strip() or line.lstrip().startswith("DEVICE"):
                continue
            parts = line.split()
            if len(parts) < 3:
                continue
            iface = parts[0]
            state = parts[2].lower()
            if iface == "lo":
                continue
            facts.interfaces.append(NetworkInterfaceFacts(
                interface_name=iface,
                configured=state in {"connected", "connecting"},
                active_connection=state == "connected",
                carrier=True if state == "connected" else None,
                operational_state=state,
            ))

    known = {i.interface_name for i in facts.interfaces}
    for path, text in archive.glob_text("sos_commands/networking/ethtool_*"):
        iface = path.split("ethtool_", 1)[-1]
        if iface == "lo":
            continue
        speed = _parse_speed(text)
        link = _parse_link(text)
        match = next((i for i in facts.interfaces if i.interface_name == iface), None)
        if match:
            match.speed_mbps = speed
            if link is not None:
                match.carrier = link
        elif iface not in known:
            facts.interfaces.append(NetworkInterfaceFacts(interface_name=iface, carrier=link, speed_mbps=speed))
            known.add(iface)
        facts.evidence_paths.append(path)
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


def _parse_speed(text: str) -> int | None:
    m = re.search(r"Speed:\s*(\d+)Mb/s", text, re.I)
    return int(m.group(1)) if m else None


def _parse_link(text: str) -> bool | None:
    m = re.search(r"Link detected:\s*(yes|no)", text, re.I)
    if not m:
        return None
    return m.group(1).lower() == "yes"
