from __future__ import annotations

import json
from pathlib import Path

import typer

from sosdiag.batch import analyze_corpus, discover_sosreports
from sosdiag.renderer.html import render_html
from sosdiag.reporting import build_report, corpus_run_summary, load_report_metadata
from sosdiag.runner import analyze_source

app = typer.Typer(help="Analyze RHEL sosreports and generate HTML structure-diagnostic reports.")


@app.command()
def analyze(
    source: str,
    format: str = typer.Option("html", "--format"),
    output_dir: str = typer.Option("output", "--output-dir"),
    metadata: str | None = typer.Option(None, "--metadata"),
) -> None:
    """Analyze one sosreport and generate JSON plus an HTML report."""
    payload = analyze_source(source)

    outdir = Path(output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    json_output = outdir / "analysis.json"
    json_output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    requested = {item.strip().lower() for item in format.split(",") if item.strip()}
    unsupported = requested - {"html", "json"}
    if unsupported:
        raise typer.BadParameter(f"unsupported format(s): {', '.join(sorted(unsupported))}; supported: html,json")

    typer.echo(f"source={source}")
    typer.echo(f"analysis={json_output}")

    if "html" in requested:
        report = build_report([payload], load_report_metadata(metadata))
        html_output = render_html(report, outdir / "report.html")
        typer.echo(f"html={html_output}")


@app.command("analyze-corpus")
def analyze_corpus_command(
    source_dir: str,
    output_dir: str = typer.Option("output", "--output-dir"),
    format: str = typer.Option("html", "--format"),
    metadata: str | None = typer.Option(None, "--metadata"),
) -> None:
    """Analyze all sosreport archives in a directory and generate one integrated HTML report."""
    sources = discover_sosreports(source_dir)
    payload = analyze_corpus(sources)

    outdir = Path(output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    json_output = outdir / "corpus-analysis.json"
    json_output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    requested = {item.strip().lower() for item in format.split(",") if item.strip()}
    unsupported = requested - {"html", "json"}
    if unsupported:
        raise typer.BadParameter(f"unsupported format(s): {', '.join(sorted(unsupported))}; supported: html,json")

    typer.echo(f"source_dir={source_dir}")
    typer.echo(f"discovered={len(sources)}")
    typer.echo(f"analyzed={payload['analyzed_count']}")
    typer.echo(f"errors={payload['error_count']}")
    typer.echo(f"analysis={json_output}")

    if "html" in requested:
        report = build_report(
            payload.get("payloads", []),
            load_report_metadata(metadata),
            run_summary=corpus_run_summary(payload),
        )
        html_output = render_html(report, outdir / "report.html")
        typer.echo(f"html={html_output}")


if __name__ == "__main__":
    app()
