from __future__ import annotations

import json
from pathlib import Path

import typer

from sosdiag.batch import analyze_corpus, discover_sosreports
from sosdiag.runner import analyze_source

app = typer.Typer(help="Analyze RHEL sosreports and generate structure-diagnostic reports.")


@app.command()
def analyze(
    source: str,
    format: str = typer.Option("html,docx", "--format"),
    output_dir: str = typer.Option("output", "--output-dir"),
) -> None:
    """Read one sosreport and emit normalized facts plus implemented diagnostics."""
    payload = analyze_source(source)

    outdir = Path(output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    output = outdir / "analysis.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    typer.echo(f"source={source}")
    typer.echo(f"requested_format={format}")
    typer.echo(f"analysis={output}")


@app.command("analyze-corpus")
def analyze_corpus_command(
    source_dir: str,
    output_dir: str = typer.Option("output", "--output-dir"),
) -> None:
    """Analyze all sosreport archives in a directory and aggregate status distribution."""
    sources = discover_sosreports(source_dir)
    payload = analyze_corpus(sources)

    outdir = Path(output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    output = outdir / "corpus-analysis.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    typer.echo(f"source_dir={source_dir}")
    typer.echo(f"discovered={len(sources)}")
    typer.echo(f"analyzed={payload['analyzed_count']}")
    typer.echo(f"errors={payload['error_count']}")
    typer.echo(f"analysis={output}")


if __name__ == "__main__":
    app()
