from __future__ import annotations

import json
from pathlib import Path

import typer

from sosdiag.archive import SosArchive
from sosdiag.diagnostics.system_basics import evaluate_boot_mode, evaluate_filesystem, evaluate_lifecycle
from sosdiag.parser.host import parse_host_facts
from sosdiag.parser.system_basics import (
    parse_boot_mode_facts,
    parse_filesystem_facts,
    parse_hardware_certification_facts,
    parse_lifecycle_facts,
)

app = typer.Typer(help="Analyze RHEL sosreports and generate structure-diagnostic reports.")


@app.command()
def analyze(
    source: str,
    format: str = typer.Option("html,docx", "--format"),
    output_dir: str = typer.Option("output", "--output-dir"),
) -> None:
    """Read a sosreport and emit normalized host facts and initial diagnostics."""
    archive = SosArchive(source)
    host = parse_host_facts(archive)

    hardware = parse_hardware_certification_facts(host)
    lifecycle = evaluate_lifecycle(parse_lifecycle_facts(host))
    boot_mode = evaluate_boot_mode(parse_boot_mode_facts(archive))
    filesystem = evaluate_filesystem(parse_filesystem_facts(archive))

    payload = {
        "host": host.model_dump(),
        "hardware_certification_facts": hardware.model_dump(),
        "diagnostics": [
            lifecycle.model_dump(),
            boot_mode.model_dump(),
            filesystem.model_dump(),
        ],
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
