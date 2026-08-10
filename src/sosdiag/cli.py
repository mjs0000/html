import typer

app = typer.Typer(help="Analyze RHEL sosreports and generate structure-diagnostic reports.")


@app.command()
def analyze(
    source: str,
    format: str = typer.Option("html,docx", "--format"),
    output_dir: str = typer.Option("output", "--output-dir"),
) -> None:
    """Analyze a sosreport archive or directory. Implementation pending PoC."""
    typer.echo(f"source={source} format={format} output_dir={output_dir}")


if __name__ == "__main__":
    app()
