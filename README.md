# sosreport Structure Diagnostic

Python-based RHEL sosreport analysis tool that parses sosreport data, evaluates diagnostic rules, and generates integrated hostname-centric HTML health-check reports.

## Target workflow

The application runs as a small FastAPI web service on Linux with Podman.

```text
Browser
  -> enter report metadata
  -> upload one or many sosreport archives
  -> Python parser + diagnostic engine
  -> integrated hostname-centric HTML report
  -> view or download report.html and corpus-analysis.json
```

DOCX generation is intentionally deferred until the HTML report and diagnostic output are validated against the real sosreport corpus.

Report metadata such as customer, execution period, sales representative, customer contact, and technical engineers is entered separately from sosreport data.

Diagnostic results use `PASS`, `WARN`, `FAIL`, and `SKIPPED`. A/B/C grades are not used. `SKIPPED` means non-applicable or insufficient evidence according to the individual rule; it is not a failure. Customer-facing host detail hides most SKIPPED items by default, while diagnostics such as 3.1 Hardware Certification may remain visible when pending external reference is itself meaningful.

For multi-host diagnostics, hostname is the primary report key. The integrated HTML report is designed for the current 59-host corpus and larger future batches.

## CLI HTML workflow

Single sosreport:

```bash
sosdiag analyze sosreport-host.tar.xz \
  --metadata examples/report-info.yaml \
  --output-dir output
```

Generated output:

```text
output/
├── analysis.json
└── report.html
```

Multiple sosreports in one directory:

```bash
sosdiag analyze-corpus /path/to/sosreports \
  --metadata examples/report-info.yaml \
  --output-dir output
```

For the current production corpus, use the strict preflight/error mode so a missing archive or per-archive analysis failure cannot be mistaken for a complete 59-host run:

```bash
sosdiag analyze-corpus /path/to/59-sosreports \
  --metadata examples/report-info.yaml \
  --output-dir output \
  --expected-count 59 \
  --fail-on-error
```

`--expected-count 59` aborts before analysis when discovery does not return exactly 59 archives. `--fail-on-error` still writes `corpus-analysis.json` and `report.html`, but exits non-zero when any archive failed so automation can detect an incomplete production run.

Generated output:

```text
output/
├── corpus-analysis.json
└── report.html
```

The corpus HTML contains target-system inventory, Hardware Certification status, analysis run summary, per-diagnostic PASS/WARN/FAIL/SKIPPED distribution, WARN/FAIL cause aggregation, hostname-centric result summary, host index, and host detail sections.

## FastAPI web workflow

Start without a container:

```bash
sosdiag-web
```

or:

```bash
uvicorn sosdiag.web.app:app --host 0.0.0.0 --port 8000
```

The web application accepts multiple sosreport archives and executes `analyze_corpus()` once. `corpus-analysis.json` and `report.html` are generated from the same production batch payload.

The service exposes:

```text
GET  /health
GET  /
POST /reports
GET  /reports/{job_key}/{filename}
```

## Podman deployment

```bash
git clone https://github.com/mjs0000/html.git
cd html
git checkout agent/initialize-sosdiag-structure
sh run.sh
```

Default runtime configuration:

```text
Host port:       8080
Container port:  8000
Host data path:  /data/sosdiag-data
Container data:  /data
```

Persistent output layout:

```text
/data/sosdiag-data/
├── uploads/
│   └── <customer_date_job>/
└── output/
    └── <customer_date_job>/
        ├── corpus-analysis.json
        └── report.html
```

The container runs as a non-root user and uses `SOSDIAG_DATA_DIR=/data`. A container health check calls `/health` every 30 seconds. `run.sh` waits up to 60 seconds for the container to become healthy before reporting success.

Runtime values may be overridden when invoking the script:

```bash
PORT=8088 DATA_DIR=/srv/sosdiag IMAGE=my-sosdiag CONTAINER=my-sosdiag sh run.sh
```

Useful commands:

```bash
podman logs -f sosdiag
podman ps --filter name=sosdiag
podman inspect --format '{{.State.Health.Status}}' sosdiag
podman stop sosdiag
podman restart sosdiag
podman rm -f sosdiag
```

## Current implementation status

Implemented or substantially implemented:

- sosreport archive reader without full extraction
- host fact normalization
- System 3.1-3.18 diagnostic parsers/evaluators/report integration
- Network 4.1-4.3 diagnostic parsers/evaluators
- Storage 5.1 Multipath parser/evaluator with explicit `dm_status`, `checker_status`, and `path_status` preservation
- single-host analysis runner
- corpus batch analyzer
- common report model
- integrated multi-host HTML report path
- hostname inventory, status distribution, WARN/FAIL cause aggregation, host index, and detailed diagnostic HTML tables
- FastAPI multi-upload -> production batch analysis -> HTML/JSON download wiring
- UBI9/Python 3.11 Containerfile with non-root runtime and health check
- Podman run script with persistent volume and health wait
- corpus CLI preflight with expected archive count and strict per-archive error exit mode

Still incomplete or requiring validation:

- full 59-host production `analyze-corpus` execution after the latest parser/report changes
- 3.1 Hardware Certification external Red Hat certification reference provider
- final customer-facing HTML layout refinement using real 59-host production output
- real Podman build/start/upload/download execution on a host with Podman
- DOCX renderer, deferred until after HTML completion

## Project goals

- Parse one or more RHEL sosreports.
- Normalize collected system data into a common model.
- Evaluate structure-diagnostic rules defined in YAML.
- Generate one integrated hostname-centric HTML report for multi-host input.
- Preserve the current RockPLACE RHEL diagnostic item set.
- Validate report status and evidence against the real sosreport corpus before finalizing presentation.
- Add DOCX only after HTML/report-model behavior is stable.
