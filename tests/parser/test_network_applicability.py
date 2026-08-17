from __future__ import annotations

import io
import tarfile
from pathlib import Path

from sosdiag.archive import SosArchive
from sosdiag.parser.network_storage import parse_network_kernel_facts


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
