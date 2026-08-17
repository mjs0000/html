from __future__ import annotations

import json
from pathlib import Path

import typer

from sosdiag.archive import SosArchive
from sosdiag.parser.host import parse_host_facts

app = typer.Typer(help="Analyze RHEL sosreports and generate structure-diagnostic reports.")


@app.command()
def analyze(
    source: str,
    format: str = typer.Option("html,docx", "--format"),
    output_dir: str = typer.Option("output", "--output-dir"),
) -> None:
    """Read a sosreport and emit the first normalized host facts JSON."""
    archive = SosArchive(source)
    facts = parse_host_facts(archive)

    outdir = Path(output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    output = outdir / "host-facts.json"
    output.write_text(json.dumps(facts.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")

    typer.echo(f"source={source}")
    typer.echo(f"requested_format={format}")
    typer.echo(f"host_facts={output}")


if __name__ == "__main__":
    app()
