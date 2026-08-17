# sosreport Structure Diagnostic

Python-based RHEL sosreport analysis tool that parses sosreport data, evaluates diagnostic rules, and generates HTML health-check reports.

## Target workflow

The application is intended to run as a small web service on Linux with Podman.

```text
Browser
  -> enter report metadata
  -> upload one or many sosreport archives
  -> Python parser + diagnostic engine
  -> integrated hostname-centric HTML report
  -> view or download the generated HTML
```

DOCX generation is intentionally deferred until the HTML report and diagnostic output are validated against the real sosreport corpus.

Report metadata such as customer, execution period, sales representative, customer contact, and technical engineers is entered separately from sosreport data.

Diagnostic results use `PASS`, `WARN`, `FAIL`, and `SKIPPED`. A/B/C grades are not used. `SKIPPED` means non-applicable or insufficient evidence according to the individual rule; it is not a failure. Customer-facing host detail hides ordinary SKIPPED items by default. `SYS_HW_CERT` is an exception: its pending/SKIPPED state remains visible because external Red Hat certification reference availability is part of the diagnostic meaning.

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

Generated output:

```text
output/
├── corpus-analysis.json
└── report.html
```

The corpus HTML contains target-system inventory, a dedicated Hardware Certification section, analysis run summary, per-diagnostic PASS/WARN/FAIL/SKIPPED distribution, aggregated WARN/FAIL causes, hostname-centric result summary, host index, and host detail sections.

## Podman target

```bash
git clone https://github.com/mjs0000/html.git
cd html
git checkout agent/initialize-sosdiag-structure
sh run.sh
```

The web/container path is still being aligned with the production parser and integrated HTML renderer. Container/browser workflow must not be considered complete until the real corpus has been executed end-to-end.

Default persistent data path:

```text
/data/sosdiag-data/
├── uploads/
└── output/
```

## Current implementation status

Implemented or substantially implemented:

- sosreport archive reader without full extraction
- host fact normalization
- System 3.1-3.18 diagnostic parsers/evaluators/report items
- Network 4.1-4.3 diagnostic parsers/evaluators
- Storage 5.1 Multipath diagnostic parser/evaluator
- 3.1 H/W identification from dmidecode with lscpu/lspci supporting evidence
- 3.1 transparent pending state when an external Red Hat Hardware Certification provider is not configured
- single-host analysis runner
- corpus batch analyzer
- common report model
- single-host HTML renderer
- integrated multi-host HTML report path
- hostname inventory, status distribution, aggregated issue causes, host index, and detailed diagnostic HTML tables
- dedicated Hardware Certification HTML section that keeps SKIPPED/Pending visible
- FastAPI/Podman skeleton

Still incomplete or requiring validation:

- full 59-host production `analyze-corpus` execution after the latest parser changes
- authoritative Red Hat Hardware Certification reference provider/query integration for 3.1
- final customer-facing HTML layout refinement using real 59-host production output
- production FastAPI upload -> analysis -> integrated HTML wiring and verification
- Podman end-to-end verification
- DOCX renderer, deferred until after HTML completion

## Project goals

- Parse one or more RHEL sosreports.
- Normalize collected system data into a common model.
- Evaluate structure-diagnostic rules defined in YAML.
- Generate one integrated hostname-centric HTML report for multi-host input.
- Preserve the current RockPLACE RHEL diagnostic item set.
- Validate report status and evidence against the real sosreport corpus before finalizing presentation.
- Add DOCX only after HTML/report-model behavior is stable.
