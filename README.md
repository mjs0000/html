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

Diagnostic results use `PASS`, `WARN`, `FAIL`, and `SKIPPED`. A/B/C grades are not used. If required sosreport evidence is insufficient, the item is retained internally as `SKIPPED` and is omitted from the customer report by default.

For multi-host diagnostics, hostname is the primary report key. The report is designed to compare at least five or more RHEL hosts in one diagnostic section.

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
- SELinux parser/diagnostic proof of concept with version-specific RHEL handling

SELinux currently uses runtime state, `/etc/selinux/config`, RHEL major-version evidence, and `/proc/cmdline`. For RHEL 9 and later, `/proc/cmdline` is required and the exact `selinux=0` token is checked before the disabled policy can be considered satisfied.

The current generated HTML/DOCX content is still a **workflow-validation report**, not the final diagnostic report. The production archive reader, full diagnostic rule set, multi-host aggregation, and final RockPLACE report rendering are the next implementation phase.

## Project goals

- Parse one or more RHEL sosreports.
- Normalize collected system data into a common model.
- Evaluate structure-diagnostic rules defined in YAML.
- Generate HTML and DOCX reports from the same diagnostic result model.
- Preserve the broader current RockPLACE RHEL diagnostic item set.
- Present results using the established RockPLACE Health Check report style.
