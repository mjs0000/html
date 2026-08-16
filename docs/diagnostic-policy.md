# Diagnostic Policy

## Report basis
The diagnostic scope follows the provided RockPLACE RHEL structure-diagnostic document, while the customer-facing report presentation follows the prior RockPLACE Health Check style: overview, summary, detailed review opinion, inspection results, and remediation guidance.

The current, broader diagnostic item set is retained. The prior Health Check report is used as a presentation reference, not as a reduced diagnostic scope.

## Evaluation status
Diagnostic results use only the following statuses:

- `PASS`: the collected evidence matches the diagnostic policy.
- `WARN`: the collected evidence does not match the recommended policy or requires review.
- `FAIL`: a rule explicitly defines the detected state as a failure condition.
- `SKIPPED`: the evidence is missing, ambiguous, or insufficient for a reliable decision.

A/B/C customer grades are not used.

## Missing or insufficient sosreport data
If required sosreport evidence is absent, ambiguous, or insufficient for a reliable automated decision:

1. The engine records the item internally as `SKIPPED`.
2. The item is excluded from customer-facing HTML/DOCX reports by default.
3. Missing data must never silently become `PASS`, `WARN`, or `FAIL`.
4. Internal JSON/debug output should retain the reason for the skip so developers can distinguish unsupported analysis from parser defects.

## Version-specific rules
When a diagnostic rule differs by RHEL major version, the engine must identify the RHEL major version before evaluating that rule. If the version cannot be determined reliably, the version-specific diagnostic is `SKIPPED`.

For SELinux specifically, RHEL 9 and later require `/proc/cmdline` evidence and inspection of the exact `selinux=0` kernel parameter. Runtime state and `/etc/selinux/config` remain supporting evidence, but configuration alone must not produce `PASS` for a RHEL 9+ host when `/proc/cmdline` is unavailable.

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
3. Hostname-based system status or inspection table
4. Inspection details
5. Recommended values / criteria
6. Remediation or action guidance
7. Evidence (optional in the main report; may be collapsible in HTML or moved to an appendix in DOCX)

For multi-host reports, hostname is the primary row key and at least five or more hosts may be compared in one diagnostic section.

## Evidence-first rule
Every automated result must retain the sosreport source path(s) and the specific parsed evidence used to reach the result, even when the evidence is hidden from the primary customer view.

## Renderer consistency
HTML and DOCX outputs must consume the same report model so that statuses, values, findings, recommendations, tables, and remediation text remain identical across formats.
