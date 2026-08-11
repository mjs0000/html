# sosreport Structure Diagnostic

Python-based RHEL sosreport analysis tool that parses sosreport data, evaluates diagnostic rules, and generates HTML/DOCX health-check reports.

## Target workflow

The application is intended to run as a small web service on Linux with Podman.

```text
Browser
  -> enter report metadata
  -> upload one or many sosreport archives
  -> choose HTML / DOCX / both
  -> Python parser + diagnostic engine
  -> download generated report(s)
```

Report metadata such as customer, execution period, sales representative, customer contact, and technical engineers is entered separately from sosreport data.

Customer-facing diagnostic grades are `A`, `B`, and `C`. If required sosreport evidence is insufficient, the item is retained internally as `SKIPPED` and is omitted from the customer report by default.

## Podman quick start

```bash
git clone https://github.com/mjs0000/html.git
cd html
git checkout agent/initialize-sosdiag-structure
sh run.sh
```

Then open:

```text
http://localhost/
```

Default persistent data path:

```text
/data/sosdiag-data/
├── uploads/
└── output/
```

Useful commands:

```bash
podman logs -f sosdiag
podman ps --filter name=sosdiag
podman stop sosdiag
podman restart sosdiag
podman rm -f sosdiag
```

## Current implementation status

The repository contains a runnable FastAPI/Podman web skeleton with:

- single or multiple sosreport upload
- separate customer/execution/sales/engineer input form
- HTML / DOCX / both selector
- persistent upload/output directories
- health endpoint at `/health`
- actual downloadable HTML and DOCX files for validating the full browser/container/output workflow

The current generated HTML/DOCX content is a **workflow-validation report**, not the final diagnostic report. It contains entered report metadata and uploaded sosreport filenames. The production sosreport parser, full diagnostic rule set, A/B/C evaluation, aggregation, and final RockPLACE report rendering are the next implementation phase.

## Project goals

- Parse one or more RHEL sosreports.
- Normalize collected system data into a common model.
- Evaluate structure-diagnostic rules defined in YAML.
- Generate HTML and DOCX reports from the same diagnostic result model.
- Preserve the broader current RockPLACE RHEL diagnostic item set.
- Present results using the established RockPLACE Health Check report style.
