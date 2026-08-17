from __future__ import annotations

import json
from pathlib import Path

import typer

from sosdiag.runner import analyze_source

app = typer.Typer(help="Analyze RHEL sosreports and generate structure-diagnostic reports.")


@app.command()
def analyze(
    source: str,
    format: str = typer.Option("html,docx", "--format"),
    output_dir: str = typer.Option("output", "--output-dir"),
) -> None:
    """Read a sosreport and emit normalized facts plus implemented diagnostics."""
    payload = analyze_source(source)

    outdir = Path(output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    output = outdir / "analysis.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    typer.echo(f"source={source}")
    typer.echo(f"requested_format={format}")
    typer.echo(f"analysis={output}")


if __name__ == "__main__":
    app()
