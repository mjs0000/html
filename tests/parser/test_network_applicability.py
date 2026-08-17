from __future__ import annotations

import io
import tarfile
from pathlib import Path

from sosdiag.archive import SosArchive
from sosdiag.diagnostics.network_storage import evaluate_netstate
from sosdiag.model.network_storage import NetstateFacts, NetworkInterfaceFacts
from sosdiag.parser.network_storage import parse_network_kernel_facts, parse_netstate_facts


def _write_archive(tmp_path: Path, files: dict[str, str]) -> Path:
    archive_path = tmp_path / "sosreport-net.tar"
    root = "sosreport-net"
    with tarfile.open(archive_path, "w") as tf:
        for path, text in files.items():
            payload = text.encode()
            info = tarfile.TarInfo(f"{root}/{path}")
            info.size = len(payload)
            tf.addfile(info, io.BytesIO(payload))
    return archive_path


def test_bond_interface_does_not_trigger_10g_kernel_applicability(tmp_path: Path) -> None:
    archive = SosArchive(_write_archive(tmp_path, {
        "sos_commands/networkmanager/nmcli_dev": "DEVICE TYPE STATE CONNECTION\nbond0 bond connected bond0\nens1 ethernet connected bond0-slave\n",
        "sos_commands/networkmanager/nmcli_con_--active": "NAME UUID TYPE DEVICE\nbond0 u1 bond bond0\nbond0-slave u2 ethernet ens1\n",
        "sos_commands/networking/ethtool_bond0": "Speed: 10000Mb/s\nLink detected: yes\n",
        "sos_commands/networking/ethtool_ens1": "Speed: 1000Mb/s\nLink detected: yes\n",
        "sos_commands/kernel/sysctl_-a": "net.core.netdev_budget = 300\n",
    }))

    facts = parse_network_kernel_facts(archive)
    assert facts.qualifying_interface is None
    assert facts.configured is None


def test_active_physical_ethernet_can_trigger_10g_kernel_applicability(tmp_path: Path) -> None:
    archive = SosArchive(_write_archive(tmp_path, {
        "sos_commands/networkmanager/nmcli_dev": "DEVICE TYPE STATE CONNECTION\nens1 ethernet connected prod\n",
        "sos_commands/networkmanager/nmcli_con_--active": "NAME UUID TYPE DEVICE\nprod u1 ethernet ens1\n",
        "sos_commands/networking/ethtool_ens1": "Speed: 25000Mb/s\nLink detected: yes\n",
        "sos_commands/kernel/sysctl_-a": "net.core.netdev_budget = 300\n",
    }))

    facts = parse_network_kernel_facts(archive)
    assert facts.qualifying_interface == "ens1"
    assert facts.speed_mbps == 25000
    assert facts.link_up is True
    assert facts.configured is True


def test_disconnected_physical_ethernet_does_not_trigger_10g(tmp_path: Path) -> None:
    archive = SosArchive(_write_archive(tmp_path, {
        "sos_commands/networkmanager/nmcli_dev": "DEVICE TYPE STATE CONNECTION\nens1 ethernet disconnected --\n",
        "sos_commands/networkmanager/nmcli_con_--active": "NAME UUID TYPE DEVICE\n",
        "sos_commands/networking/ethtool_ens1": "Speed: 10000Mb/s\nLink detected: yes\n",
        "sos_commands/kernel/sysctl_-a": "net.core.netdev_budget = 300\n",
    }))

    facts = parse_network_kernel_facts(archive)
    assert facts.qualifying_interface is None


def test_unused_disconnected_port_does_not_warn_netstate() -> None:
    facts = NetstateFacts(
        networkmanager_in_use=True,
        networkmanager_active=True,
        interfaces=[
            NetworkInterfaceFacts(
                interface_name="ens1",
                configured=True,
                active_connection=True,
                carrier=True,
                operational_state="connected",
            ),
            NetworkInterfaceFacts(
                interface_name="ens2",
                configured=False,
                active_connection=False,
                carrier=False,
                operational_state="disconnected",
            ),
        ],
    )

    result = evaluate_netstate(facts)
    assert result.status == "PASS"
    assert result.current_values["link_status"] == "PASS"


def test_connected_virbr_bridge_is_not_a_netstate_failure(tmp_path: Path) -> None:
    archive = SosArchive(_write_archive(tmp_path, {
        "sos_commands/systemd/systemctl_list-units": "NetworkManager.service loaded active running Network Manager\n",
        "sos_commands/networkmanager/nmcli_dev": "DEVICE TYPE STATE CONNECTION\nens3f0 ethernet connected prod\nvirbr0 bridge connected virbr0\n",
        "sos_commands/networkmanager/nmcli_con_--active": "NAME UUID TYPE DEVICE\nprod u1 ethernet ens3f0\nvirbr0 u2 bridge virbr0\n",
        "sos_commands/networking/ethtool_ens3f0": "Speed: 1000Mb/s\nLink detected: yes\n",
        "sos_commands/networking/ethtool_virbr0": "Link detected: no\n",
    }))

    result = evaluate_netstate(parse_netstate_facts(archive))
    assert result.status == "PASS"
    assert result.current_values["link_status"] == "PASS"


def test_netstate_uses_ip_evidence_without_nmcli(tmp_path: Path) -> None:
    archive = SosArchive(_write_archive(tmp_path, {
        "sos_commands/systemd/systemctl_list-units": "NetworkManager.service loaded inactive dead Network Manager\n",
        "sos_commands/networking/ip_-o_addr": "2: ens1    inet 192.0.2.10/24 brd 192.0.2.255 scope global ens1\n3: virbr0    inet 192.168.122.1/24 brd 192.168.122.255 scope global virbr0\n",
        "sos_commands/networking/ip_route_show_table_all": "default via 192.0.2.1 dev ens1\n192.0.2.0/24 dev ens1 scope link\n192.168.122.0/24 dev virbr0 scope link\n",
        "sos_commands/networking/ip_-s_-d_link": "2: ens1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 state UP mode DEFAULT group default qlen 1000\n3: virbr0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 state DOWN mode DEFAULT group default qlen 1000\n",
        "sos_commands/networking/ethtool_ens1": "Speed: 10000Mb/s\nLink detected: yes\n",
    }))

    result = evaluate_netstate(parse_netstate_facts(archive))
    assert result.status == "PASS"
    assert result.current_values["networkmanager_status"] == "SKIPPED"
    assert result.current_values["link_status"] == "PASS"
