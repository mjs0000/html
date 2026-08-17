from __future__ import annotations

import io
import tarfile
from pathlib import Path

from sosdiag.archive import SosArchive
from sosdiag.parser.system_basics import _parse_findmnt
from sosdiag.parser.system_runtime import _kernel_package_key


def test_archive_indexes_symlinked_evidence(tmp_path: Path) -> None:
    archive_path = tmp_path / "sosreport-test.tar"
    root = "sosreport-test"
    payload = b"kernel-5.14.0-284.30.1.el9_2.x86_64\n"
    with tarfile.open(archive_path, "w") as tf:
        target = tarfile.TarInfo(f"{root}/sos_commands/rpm/packages")
        target.size = len(payload)
        tf.addfile(target, io.BytesIO(payload))

        link = tarfile.TarInfo(f"{root}/installed-rpms")
        link.type = tarfile.SYMTYPE
        link.linkname = "sos_commands/rpm/packages"
        tf.addfile(link)

    archive = SosArchive(archive_path)
    assert "installed-rpms" in archive.paths()
    assert archive.read_text("installed-rpms") == payload.decode()


def test_findmnt_ignores_pseudo_and_virtual_mounts() -> None:
    text = """
TARGET SOURCE FSTYPE OPTIONS
/ /dev/mapper/rhel-root xfs rw
/boot /dev/sda2 xfs rw
/proc proc proc rw
/sys sysfs sysfs rw
/run tmpfs tmpfs rw
/var/lib/containers overlay overlay rw
"""
    entries = _parse_findmnt(text)
    assert [(e.mount_point, e.device, e.filesystem_type) for e in entries] == [
        ("/", "/dev/mapper/rhel-root", "xfs"),
        ("/boot", "/dev/sda2", "xfs"),
    ]


def test_kernel_package_key_is_not_lexical() -> None:
    older = "kernel-5.14.0-284.9.1.el9_2.x86_64"
    newer = "kernel-5.14.0-284.30.1.el9_2.x86_64"
    assert _kernel_package_key(newer) > _kernel_package_key(older)
