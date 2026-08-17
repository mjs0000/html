from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from sosdiag.model.report import DiagnosticReport


_LARGE_REPORT_HOST_THRESHOLD = 10


def render_html(report: DiagnosticReport, output: str | Path) -> Path:
    template_root = Path(__file__).resolve().parents[3] / "templates" / "html"
    env = Environment(
        loader=FileSystemLoader(template_root),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("report.html.j2")
    rendered = template.render(
        metadata=report.metadata,
        hosts=report.hosts,
        run_summary=report.run_summary,
        large_report=len(report.hosts) > _LARGE_REPORT_HOST_THRESHOLD,
    )

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    return output_path
