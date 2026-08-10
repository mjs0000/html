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
- `src/`: implementation.
- `tests/`: executable proof of expected behavior.

## Required result states
Diagnostic implementations must distinguish at least: `A`, `B`, `C`, and `UNKNOWN` where evidence is insufficient.

## Change rule
Any diagnostic change must identify its sosreport source, parsing logic, assessment rule, evidence shown in reports, missing-data behavior, and tests.
