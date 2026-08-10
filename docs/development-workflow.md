# AI Development Workflow

1. ChatGPT analyzes the diagnostic item and updates documentation/specification.
2. Claude implements Python code and tests on a feature branch.
3. Claude opens a pull request.
4. ChatGPT reviews spec -> implementation -> tests -> report output.
5. Claude resolves review findings without changing policy silently.
6. ChatGPT performs final verification and documentation updates.

## Pull request expectations
Each diagnostic PR should include:
- diagnostic ID and section
- sosreport source files used
- parser behavior
- A/B/C/UNKNOWN criteria
- missing-data behavior
- evidence emitted into the result model
- unit tests and at least one representative fixture

## First PoC scope
Implement the complete pipeline for:
1. base system information
2. Boot Mode
3. Filesystem
4. SELinux

The PoC is complete only when the same results can be exported to JSON, HTML, and DOCX.
