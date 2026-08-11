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

## Customer-facing grades
Customer-facing HTML/DOCX reports use only `A`, `B`, and `C` grades.

If sosreport evidence is missing, ambiguous, or insufficient for a reliable automated decision, the implementation must record the item internally as `SKIPPED` and exclude it from the customer-facing report by default. It must never silently convert missing evidence into an `A`, `B`, or `C` result.

## Manual report inputs
Execution information, customer/site information, RockPLACE sales representative, RockPLACE technical engineer(s), and customer contact are supplied separately from sosreport through report metadata input. Do not infer these values from sosreport.

## Report presentation
Keep the broader current diagnostic scope, while following the established RockPLACE Health Check report presentation style where practical. Detailed items should support definition, review opinion, current/system status, inspection details, recommendations, remediation, and evidence.

## Change rule
Any diagnostic change must identify its sosreport source, parsing logic, assessment rule, evidence retained, missing-data behavior, report visibility, and tests.
