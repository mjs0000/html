# AGENTS.md

## Purpose
This repository is the shared source of truth for AI-assisted development of the RHEL sosreport structure-diagnostic tool.

## Roles

### ChatGPT
- Analyze diagnostic requirements and source documents.
- Map report items to sosreport evidence.
- Define and review YAML specifications.
- Review pull requests against specifications and tests.
- Maintain final architecture and user documentation.

### Claude
- Implement Python production code from approved specifications.
- Add unit/integration tests.
- Address review findings.
- Do not change diagnostic semantics without updating the relevant specification.

## Source of truth
- `docs/`: human-readable rationale and policy.
- `spec/`: machine-readable diagnostic definitions and sosreport mappings.
- `examples/report-info.yaml`: example for manually supplied report metadata.
- `src/`: implementation.
- `tests/`: executable proof of expected behavior.

## Customer-facing status
Customer-facing HTML reports use only `PASS`, `WARN`, `FAIL`, and `SKIPPED`.

A/B/C grades are not used.

If sosreport evidence is missing, ambiguous, non-applicable, or insufficient for a reliable automated decision, the implementation must record the item as `SKIPPED`. `SKIPPED` is not a failure and must never be silently converted to `PASS`, `WARN`, or `FAIL`.

Most SKIPPED items are hidden from hostname detail by default. A diagnostic may explicitly remain visible when the missing external dependency or pending reference is itself meaningful to the report, such as 3.1 Hardware Certification while the external Red Hat certification provider is not configured.

## Manual report inputs
Execution information, customer/site information, RockPLACE sales representative, RockPLACE technical engineer(s), and customer contact are supplied separately from sosreport through report metadata input. Do not infer these values from sosreport.

## Report presentation
Keep the broader current diagnostic scope while following the established RockPLACE Health Check report presentation style where practical. Reports are hostname-centric and should support definition, review opinion, current/system status, inspection details, recommendations, remediation, and evidence.

For large multi-host reports, warning/failure summaries should aggregate repeated causes instead of repeating identical findings for every host. PASS detail remains available at hostname level.

## Change rule
Any diagnostic change must identify its sosreport source, parsing logic, assessment rule, evidence retained, missing-data behavior, report visibility, and tests.

Do not claim a test suite, Podman build, production corpus run, or external-reference validation succeeded unless it was actually executed in an environment capable of running it.
