from __future__ import annotations

from sosdiag.model.diagnostic import DiagnosticResult, Evidence, ReportTable
from sosdiag.model.network_storage import BondingFacts, MultipathFacts, NetstateFacts, NetworkKernelFacts


def evaluate_bonding(facts: BondingFacts) -> DiagnosticResult:
    if not facts.bonds:
        return DiagnosticResult(
            id="NET_BONDING", category="Network", section="4.1", title="이중화 (Bonding)",
            status="SKIPPED", summary="Bonding 구성이 없어 평가 대상이 아닙니다.", include_in_report=False,
        )
    rows = []
    overall = "PASS"
    findings: list[str] = []
    evidence: list[Evidence] = []
    for bond in facts.bonds:
        mode = (bond.mode or "").lower()
        mode_ok = any(token in mode for token in ("active-backup", "802.3ad", "dynamic link aggregation", "dynamic-link-aggregation"))
        mode_status = "PASS" if bond.mode is not None and mode_ok else ("WARN" if bond.mode is not None else "SKIPPED")
        if "active-backup" in mode:
            monitoring_status = "PASS" if bond.miimon == 100 else ("WARN" if bond.miimon is not None else "SKIPPED")
        else:
            monitoring_status = "PASS" if bond.miimon is not None else "SKIPPED"
        slave_states = [s.link_state for s in bond.slaves]
        if not bond.slaves or any(s is None for s in slave_states) or bond.mii_status is None:
            redundancy_status = "SKIPPED"
        elif len(bond.slaves) >= 2 and bond.mii_status == "up" and all(s == "up" for s in slave_states):
            redundancy_status = "PASS"
        else:
            redundancy_status = "WARN"
            findings.append(f"{bond.bond_name}: Bond 또는 Slave 이중화 상태를 확인하십시오.")
        row_statuses = {mode_status, monitoring_status, redundancy_status}
        if "WARN" in row_statuses:
            overall = "WARN"
        rows.append({
            "bond_name": bond.bond_name,
            "mode": bond.mode,
            "miimon": bond.miimon,
            "slave_count": len(bond.slaves),
            "active_slave": bond.active_slave,
            "slave_states": {s.name: s.link_state for s in bond.slaves},
            "mode_status": mode_status,
            "monitoring_status": monitoring_status,
            "redundancy_status": redundancy_status,
        })
        if bond.evidence_path:
            evidence.append(Evidence(source=bond.evidence_path, detail=f"bond={bond.bond_name}"))
    if overall == "PASS" and all("SKIPPED" in {r["mode_status"], r["monitoring_status"], r["redundancy_status"]} for r in rows):
        overall = "SKIPPED"
    return DiagnosticResult(
        id="NET_BONDING", category="Network", section="4.1", title="이중화 (Bonding)", status=overall,
        summary="모든 Slave의 Link/MII 상태와 Bond mode/monitoring을 평가합니다.", findings=findings,
        evidence=evidence, tables=[ReportTable(columns=list(rows[0].keys()), rows=rows)], include_in_report=overall != "SKIPPED",
    )


def evaluate_network_kernel(facts: NetworkKernelFacts) -> DiagnosticResult:
    if not (facts.qualifying_interface and facts.link_up is True and facts.configured is True):
        return DiagnosticResult(
            id="NET_KERNEL_PARAM", category="Network", section="4.2", title="네트워크 커널 파라미터",
            status="SKIPPED", summary="설정되어 있고 Link Up인 10G 이상 Physical Ethernet NIC가 없어 평가 대상이 아닙니다.", include_in_report=False,
            current_values=facts.model_dump(),
        )
    expected = {
        "net.core.netdev_max_backlog": ("ge", 2000),
        "net.ipv4.tcp_rmem": ("eq", [4096, 87380, 16777216]),
        "net.ipv4.tcp_wmem": ("eq", [4096, 16384, 16777216]),
        "net.core.rmem_max": ("ge", 16777216),
        "net.core.wmem_max": ("ge", 16777216),
        "vm.min_free_kbytes": ("ge", 1024000),
        "net.core.netdev_budget": ("eq", 300),
    }
    statuses: dict[str, str] = {}
    findings: list[str] = []
    for name, (op, target) in expected.items():
        value = facts.values.get(name)
        if value is None:
            statuses[name] = "SKIPPED"
            continue
        ok = value == target if op == "eq" else isinstance(value, int) and value >= int(target)
        statuses[name] = "PASS" if ok else "WARN"
        if not ok:
            findings.append(f"{name}={value} 권고값과 다릅니다.")
    status = "WARN" if "WARN" in statuses.values() else ("PASS" if statuses and all(v == "PASS" for v in statuses.values()) else "SKIPPED")
    return DiagnosticResult(
        id="NET_KERNEL_PARAM", category="Network", section="4.2", title="네트워크 커널 파라미터", status=status,
        summary=f"{facts.qualifying_interface} ({facts.speed_mbps} Mb/s) Physical Ethernet NIC 기준으로 10G 네트워크 파라미터를 평가합니다.",
        findings=findings, current_values={**facts.model_dump(), "parameter_status": statuses}, recommended_values=expected,
        evidence=[Evidence(source=p, detail="network kernel evidence") for p in facts.evidence_paths], include_in_report=status != "SKIPPED",
    )


def evaluate_netstate(facts: NetstateFacts) -> DiagnosticResult:
    nm_status = "SKIPPED"
    if facts.networkmanager_in_use is True:
        if facts.networkmanager_active is True:
            nm_status = "PASS"
        elif facts.networkmanager_active is False:
            nm_status = "WARN"

    # Only configured/in-use links are assessed. Unused disconnected ports must not create WARN.
    interfaces = [i for i in facts.interfaces if i.active_connection is True or i.configured is True]
    if interfaces:
        if any(i.carrier is False for i in interfaces):
            link_status = "WARN"
        elif all(i.carrier is True for i in interfaces):
            link_status = "PASS"
        else:
            link_status = "SKIPPED"
    else:
        link_status = "SKIPPED"

    visible = [s for s in (nm_status, link_status) if s != "SKIPPED"]
    status = "WARN" if "WARN" in visible else ("PASS" if visible else "SKIPPED")
    rows = [i.model_dump() for i in facts.interfaces]
    return DiagnosticResult(
        id="NET_NETSTATE", category="Network", section="4.3", title="Netstate", status=status,
        summary="NetworkManager 사용 여부와 실제 활성/구성 Interface의 Link 상태만 평가합니다. 미사용 disconnected 포트는 판정에서 제외합니다.",
        current_values={"networkmanager_status": nm_status, "link_status": link_status, **facts.model_dump(exclude={"interfaces"})},
        evidence=[Evidence(source=p, detail="netstate evidence") for p in facts.evidence_paths],
        tables=[ReportTable(columns=list(rows[0].keys()), rows=rows)] if rows else [], include_in_report=status != "SKIPPED",
    )


def evaluate_multipath(facts: MultipathFacts) -> DiagnosticResult:
    if not facts.maps:
        return DiagnosticResult(
            id="STG_MULTIPATH", category="Storage", section="5.1", title="Device Mapper Multipath",
            status="SKIPPED", summary="실제 Multipath Map이 없어 평가 대상이 아닙니다.", include_in_report=False,
        )
    rows = []
    findings: list[str] = []
    overall = "PASS"
    for mp in facts.maps:
        states = [(p.path_state or "").lower() for p in mp.paths]
        dm_states = [(p.dm_state or "").lower() for p in mp.paths]
        usable = sum(1 for s, d in zip(states, dm_states) if s in {"ready", "active", "up", "running"} and d not in {"failed", "faulty", "offline"})
        failed = sum(1 for s, d in zip(states, dm_states) if s in {"failed", "faulty", "offline", "down"} or d in {"failed", "faulty", "offline"})
        map_status = "WARN" if (mp.dm_state or "").lower() in {"failed", "suspended", "offline"} else "PASS"
        redundancy_status = "PASS" if len(mp.paths) >= 2 and usable >= 2 and failed == 0 else "WARN"
        config_status = "PASS" if facts.effective_config_available is True else ("SKIPPED" if facts.effective_config_available is None else "WARN")
        if "WARN" in {map_status, redundancy_status, config_status}:
            overall = "WARN"
        if redundancy_status == "WARN":
            findings.append(f"{mp.map_name}: usable path={usable}, failed path={failed}로 이중화 상태를 확인해야 합니다.")
        rows.append({
            "map_name": mp.map_name, "wwid": mp.wwid, "vendor_product": " ".join(filter(None, [mp.vendor, mp.product])),
            "total_paths": len(mp.paths), "usable_paths": usable, "failed_paths": failed,
            "map_status": map_status, "redundancy_status": redundancy_status, "config_status": config_status,
        })
    return DiagnosticResult(
        id="STG_MULTIPATH", category="Storage", section="5.1", title="Device Mapper Multipath", status=overall,
        summary="실제 Multipath Map과 모든 Path의 정상 상태/이중화를 평가합니다.", findings=findings,
        evidence=[Evidence(source=p, detail="multipath evidence") for p in facts.evidence_paths],
        tables=[ReportTable(columns=list(rows[0].keys()), rows=rows)],
    )
