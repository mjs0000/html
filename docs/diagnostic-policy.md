# Diagnostic Policy

## Report basis
The diagnostic scope follows the provided RockPLACE RHEL 9 structure-diagnostic document, while the customer-facing report presentation follows the prior RockPLACE Health Check style: overview, summary, detailed review opinion, inspection results, and remediation guidance.

The current, broader diagnostic item set is retained. The prior Health Check report is used as a presentation reference, not as a reduced diagnostic scope.

## Evaluation grades
Customer-facing reports use only the following grades:

- `A`: generally good; recommended configuration is applied.
- `B`: no immediate operational impact, but improvement should be reviewed.
- `C`: potential for issues; remediation planning is needed.

`UNKNOWN` is not a customer-facing grade.

## Missing or insufficient sosreport data
If required sosreport evidence is absent, ambiguous, or insufficient for a reliable automated decision:

1. The engine records the item internally as `SKIPPED`.
2. The item is excluded from customer-facing HTML/DOCX reports by default.
3. Missing data must never silently become `A`, `B`, or `C`.
4. Internal JSON/debug output should retain the reason for the skip so developers can distinguish unsupported analysis from parser defects.

## Manually supplied report metadata
The following values are not inferred from sosreport and must be supplied independently through a report input file such as `report-info.yaml`:

- Customer/site information
- Subscription status, when used
- Health Check execution period
- Execution location
- Customer contact
- RockPLACE sales representative
- RockPLACE technical engineer(s)

These inputs populate the report overview sections and are not diagnostic results.

## Customer-facing section structure
Each diagnostic item should support the following presentation when applicable:

1. Definition / diagnostic purpose
2. Review opinion
3. System status or inspection table
4. Inspection details
5. Recommended values / criteria
6. Remediation or action guidance
7. Evidence (optional in the main report; may be collapsible in HTML or moved to an appendix in DOCX)

## Evidence-first rule
Every automated result must retain the sosreport source path(s) and the specific parsed evidence used to reach the result, even when the evidence is hidden from the primary customer view.

## Renderer consistency
HTML and DOCX outputs must consume the same report model so that grades, values, findings, recommendations, tables, and remediation text remain identical across formats.
