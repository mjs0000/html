# Architecture

## Goal
Parse one or more RHEL sosreports and generate consistent HTML and DOCX structure-diagnostic reports from the same diagnostic result model.

## Pipeline

```text
report-info.yaml ------------------------------┐
                                               │
sosreport archive(s)                           │
  -> archive reader                            │
  -> parsers                                   │
  -> normalized models                         │
  -> diagnostic engine <- YAML mappings/rules │
  -> report model <----------------------------┘
  -> HTML renderer
  -> DOCX renderer
```

## Input responsibilities

### sosreport
Provides technical evidence such as OS, hardware, boot, filesystem, service, kernel, network, and storage facts.

### report-info.yaml
Provides non-sosreport metadata used for the report cover and overview sections, including customer/site, execution information, sales representative, technical engineers, and customer contact.

### diagnostic YAML
Defines mappings, thresholds, recommendations, and presentation metadata for diagnostic items.

## Separation of responsibilities
- Parsers extract facts from sosreport and must not decide report grades unless unavoidable.
- Rules define diagnostic policy and thresholds.
- The diagnostic engine combines normalized facts with policy.
- Renderers only format the report model and must not re-evaluate diagnostics.
- Missing/insufficient evidence is represented internally as `SKIPPED`; it is not rendered as an `UNKNOWN` grade in customer reports.

## Customer report organization
The detailed report should follow the RockPLACE Health Check presentation pattern while preserving the broader current diagnostic scope:

1. Structure Diagnostic Overview
   - Execution information
   - RockPLACE sales representative
   - RockPLACE technical engineer(s)
   - Target systems
   - Result summary
2. Detailed Report
   - System
   - Network
   - Storage

Each detailed diagnostic item may include definition, review opinion, inspection/status table, detailed findings, recommended values, remediation, and evidence.

## Multi-host support
A report may aggregate multiple sosreports. Diagnostic results therefore belong to hosts, while report sections aggregate host results for summary tables.
