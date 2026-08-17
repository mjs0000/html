from __future__ import annotations

import io
import tarfile
from pathlib import Path

from sosdiag.archive import SosArchive
from sosdiag.parser.network_storage import parse_multipath_facts


def _write_archive(tmp_path: Path, text: str) -> Path:
    archive_path = tmp_path / "sosreport-multipath.tar"
    root = "sosreport-multipath"
    payload = text.encode()
    with tarfile.open(archive_path, "w") as tf:
        info = tarfile.TarInfo(f"{root}/sos_commands/multipath/multipath_-ll")
        info.size = len(payload)
        tf.addfile(info, io.BytesIO(payload))
    return archive_path


def test_parser_preserves_dm_checker_and_path_status(tmp_path: Path) -> None:
    archive = SosArchive(_write_archive(tmp_path, """mpatha (36006016050225e0084871366dfe0e089) dm-9 DGC,VRAID
size=50G features='1 queue_if_no_path' hwhandler='1 alua' wp=rw
|-+- policy='service-time 0' prio=50 status=active
| |- 13:0:1:0  sde 8:64  active ready running
| `- 15:0:1:0  sdi 8:128 active ready running
"""))

    facts = parse_multipath_facts(archive)

    assert len(facts.maps) == 1
    assert len(facts.maps[0].paths) == 2
    first = facts.maps[0].paths[0]
    assert first.dm_status == "active"
    assert first.checker_status == "ready"
    assert first.path_status == "running"
