from __future__ import annotations

import json
from pathlib import Path

import typer

from sosdiag.archive import SosArchive
from sosdiag.diagnostics.selinux import evaluate_selinux
from sosdiag.diagnostics.system_basics import evaluate_boot_mode, evaluate_filesystem, evaluate_lifecycle
from sosdiag.diagnostics.system_runtime import evaluate_chrony, evaluate_firewalld, evaluate_kdump, evaluate_package_update
from sosdiag.parser.host import parse_host_facts
from sosdiag.parser.selinux import parse_selinux
from sosdiag.parser.system_basics import (
    parse_boot_mode_facts,
    parse_filesystem_facts,
    parse_hardware_certification_facts,
    parse_lifecycle_facts,
)
from sosdiag.parser.system_runtime import (
    parse_chrony_facts,
    parse_firewalld_facts,
    parse_kdump_facts,
    parse_package_update_facts,
)

app = typer.Typer(help="Analyze RHEL sosreports and generate structure-diagnostic reports.")


def _text(archive: SosArchive, candidates: list[str]) -> str | None:
    found = archive.first_text(candidates)
    return found[1] if found else None


@app.command()
def analyze(
    source: str,
    format: str = typer.Option("html,docx", "--format"),
    output_dir: str = typer.Option("output", "--output-dir"),
) -> None:
    """Read a sosreport and emit normalized facts plus implemented diagnostics."""
    archive = SosArchive(source)
    host = parse_host_facts(archive)

    hardware = parse_hardware_certification_facts(host)
    lifecycle = evaluate_lifecycle(parse_lifecycle_facts(host))
    boot_mode = evaluate_boot_mode(parse_boot_mode_facts(archive))
    filesystem = evaluate_filesystem(parse_filesystem_facts(archive))
    package_update = evaluate_package_update(parse_package_update_facts(archive, host))

    selinux_sources = {
        "os_release": _text(archive, ["etc/redhat-release", "etc/os-release"]),
        "getenforce": _text(archive, ["sos_commands/selinux/getenforce"]),
        "sestatus": _text(archive, ["sos_commands/selinux/sestatus", "sos_commands/selinux/sestatus_-v"]),
        "config": _text(archive, ["etc/selinux/config"]),
        "cmdline": _text(archive, ["proc/cmdline"]),
    }
    selinux = evaluate_selinux(parse_selinux(selinux_sources))
    firewalld = evaluate_firewalld(parse_firewalld_facts(archive))
    chrony = evaluate_chrony(parse_chrony_facts(archive))
    kdump = evaluate_kdump(parse_kdump_facts(archive))

    diagnostics = [
        lifecycle,
        boot_mode,
        filesystem,
        package_update,
        selinux,
        firewalld,
        chrony,
        kdump,
    ]

    payload = {
        "host": host.model_dump(),
        "hardware_certification_facts": hardware.model_dump(),
        "diagnostics": [item.model_dump() for item in diagnostics],
    }

    outdir = Path(output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    output = outdir / "analysis.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    typer.echo(f"source={source}")
    typer.echo(f"requested_format={format}")
    typer.echo(f"analysis={output}")


if __name__ == "__main__":
    app()
