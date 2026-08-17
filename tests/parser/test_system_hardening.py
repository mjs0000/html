from __future__ import annotations

from pathlib import Path

from sosdiag.archive import SosArchive
from sosdiag.parser.system_mid import parse_coredump_facts, parse_error_log_facts
from sosdiag.parser.systemd import parse_systemd_unit_state


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_systemd_static_is_unknown_not_disabled(tmp_path: Path) -> None:
    root = tmp_path / "sosreport-test"
    _write(root, "sos_commands/systemd/systemctl_list-unit-files", "demo.service static\n")
    _write(root, "sos_commands/systemd/systemctl_list-units_--all", "demo.service loaded inactive dead Demo\n")

    state = parse_systemd_unit_state(SosArchive(root), "demo.service")

    assert state.enablement_state == "static"
    assert state.enabled is None
    assert state.active is False


def test_error_log_single_timeout_is_not_actionable(tmp_path: Path) -> None:
    root = tmp_path / "sosreport-test"
    _write(root, "var/log/messages", "Aug 1 host app[1]: request timeout id=123\n")

    facts = parse_error_log_facts(SosArchive(root))

    assert facts.usable_sources == ["var/log/messages"]
    assert facts.findings == []


def test_error_log_repeated_timeout_is_warn_finding(tmp_path: Path) -> None:
    root = tmp_path / "sosreport-test"
    _write(
        root,
        "var/log/messages",
        "\n".join(
            [
                "Aug 1 host storage[1]: command timeout id=100",
                "Aug 1 host storage[1]: command timeout id=101",
                "Aug 1 host storage[1]: command timeout id=102",
            ]
        ),
    )

    facts = parse_error_log_facts(SosArchive(root))

    assert len(facts.findings) == 1
    assert facts.findings[0].severity == "WARN"
    assert facts.findings[0].signature == "repeated timeout"
    assert facts.findings[0].count == 3


def test_coredump_retention_requires_positive_override(tmp_path: Path) -> None:
    root = tmp_path / "sosreport-test"
    _write(root, "etc/tmpfiles.d/coredump.conf", "d /var/lib/systemd/coredump 0755 root root 3d\n")

    facts = parse_coredump_facts(SosArchive(root))

    assert facts.retention_override is False


def test_coredump_retention_accepts_explicit_exclusion(tmp_path: Path) -> None:
    root = tmp_path / "sosreport-test"
    _write(root, "etc/tmpfiles.d/coredump.conf", "x /var/lib/systemd/coredump\n")

    facts = parse_coredump_facts(SosArchive(root))

    assert facts.retention_override is True
