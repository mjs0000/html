# Diagnostic Policy

## Report basis
The initial report organization follows the provided RockPLACE RHEL 9 structure-diagnostic scope document: overview, summary, System, Network, and Storage.

## Evaluation grades
- `A`: generally good; recommended configuration is applied.
- `B`: no immediate operational impact, but improvement should be reviewed.
- `C`: potential for issues; remediation planning is needed.
- `UNKNOWN`: sosreport evidence is absent, ambiguous, or insufficient for a reliable decision.

## Evidence-first rule
Every automated result must retain the sosreport source path(s) and the specific parsed evidence used to reach the result.

## Missing data
Missing data must never silently become `A`. Return `UNKNOWN` unless a rule explicitly defines another safe interpretation.

## Renderer consistency
HTML and DOCX outputs must consume the same report model so that values, grades, findings, and recommendations remain identical across formats.
