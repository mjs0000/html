from __future__ import annotations

from html import escape
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
    issue_summary = _render_issue_summary(report)
    if issue_summary:
        rendered = rendered.replace(
            '<section id="diagnostic-summary">',
            issue_summary + '\n    <section id="diagnostic-summary">',
            1,
        )

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    return output_path


def _render_issue_summary(report: DiagnosticReport) -> str:
    summary = report.run_summary
    if summary is None or not summary.issue_distribution:
        return ""

    rows: list[str] = []
    for diagnostic_id, issues in summary.issue_distribution.items():
        for issue_key, aggregate in issues.items():
            affected = aggregate.warn_count + aggregate.fail_count
            if affected <= 0:
                continue
            host_preview = ", ".join(aggregate.hosts[:8])
            if len(aggregate.hosts) > 8:
                host_preview += f" 외 {len(aggregate.hosts) - 8}대"
            rows.append(
                "<tr>"
                f"<td><strong>{escape(diagnostic_id)}</strong></td>"
                f"<td><code>{escape(issue_key)}</code></td>"
                f"<td class=\"WARN\">{aggregate.warn_count}</td>"
                f"<td class=\"FAIL\">{aggregate.fail_count}</td>"
                f"<td>{escape(host_preview or '-')}</td>"
                "</tr>"
            )

    if not rows:
        return ""

    return (
        '    <section id="issue-summary">\n'
        '      <h2>3.2 주요 WARN/FAIL 원인 요약</h2>\n'
        '      <p class="section-note">반복되는 경고를 Host별로 나열하지 않고, 구조화된 하위 판정값을 기준으로 원인별 영향 Host 수를 집계합니다.</p>\n'
        '      <div class="wide">\n'
        '        <table>\n'
        '          <tr><th>Diagnostic ID</th><th>원인 항목</th><th>WARN Host</th><th>FAIL Host</th><th>대표 Host</th></tr>\n'
        + "\n".join("          " + row for row in rows)
        + '\n        </table>\n'
        '      </div>\n'
        '    </section>'
    )
