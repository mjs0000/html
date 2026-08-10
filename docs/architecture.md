# Architecture

## Goal
Parse one or more RHEL sosreports and generate consistent HTML and DOCX structure-diagnostic reports from the same diagnostic result model.

## Pipeline

```text
sosreport archive(s)
  -> archive reader
  -> parsers
  -> normalized models
  -> diagnostic engine <- YAML mappings/rules
  -> report model
  -> HTML renderer
  -> DOCX renderer
```

## Separation of responsibilities
- Parsers extract facts from sosreport and must not decide report grades unless unavoidable.
- Rules define diagnostic policy and thresholds.
- The diagnostic engine combines normalized facts with policy.
- Renderers only format the report model and must not re-evaluate diagnostics.

## Multi-host support
A report may aggregate multiple sosreports. Diagnostic results therefore belong to hosts, while report sections aggregate host results for summary tables.
