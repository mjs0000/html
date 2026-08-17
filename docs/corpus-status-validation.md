# 59-host corpus status validation

This document records an independent, single-pass validation of selected diagnostics against the current 59-sosreport corpus.

## Scope and method

- Corpus size: 59 sosreport archives.
- Processing errors: 0.
- Validation was performed by streaming each tar.xz once and extracting only the evidence required by the selected rules.
- Status vocabulary is limited to PASS, WARN, FAIL, and SKIPPED.
- These figures are intended as corpus validation evidence. They must not replace the production `sosdiag` runner when final customer-facing reports are generated.

## Selected diagnostic distribution

| Diagnostic | PASS | WARN | FAIL | SKIPPED |
|---|---:|---:|---:|---:|
| SYS_SELINUX (3.6) | 55 | 4 | 0 | 0 |
| SYS_TIME_SYNC (3.8) | 0 | 54 | 0 | 5 |
| SYS_KDUMP (3.9) | 24 | 35 | 0 | 0 |
| NET_BONDING (4.1) | 33 | 0 | 0 | 26 |
| NET_KERNEL_PARAM (4.2) | 0 | 49 | 0 | 10 |
| NET_NETSTATE (4.3) | 53 | 6 | 0 | 0 |
| STG_MULTIPATH (5.1) | 6 | 0 | 0 | 53 |

## Host-level exceptions and applicability

### 3.6 SELinux

WARN hosts:

- FDID-GW-TS
- FDID-NODE-TS1
- FDID-NODE-TS2
- FDID-NODE-TS3

All other 55 hosts satisfied the project-disabled SELinux policy in the independently validated evidence set.

### 3.8 Time Sync

- 54 hosts evaluated WARN under the project policy requiring an active Chrony service and at least four configured sources.
- 5 hosts were SKIPPED because the required service/configuration evidence was incomplete for a deterministic result.
- No host was promoted to PASS from selected-source state alone; configured source count remains the criterion.

### 3.9 Kdump

- 24 hosts evaluated PASS.
- 35 hosts evaluated WARN when the combined Kdump state/reservation and required Kdump-related sysctl checks were applied.
- `kdumpctl showmem` is not required for PASS because the current corpus does not consistently contain it.

### 4.1 Bonding

- 33 hosts contain actual Bonding evidence and evaluated PASS in the independent validation.
- 26 hosts have no Bonding configuration and are therefore SKIPPED/non-applicable.
- The real corpus commonly stores Bonding data under `proc/<pid>/net/bonding/*`; the parser must support this path family.

### 4.2 Network Kernel Parameters

- 49 hosts met the configured, link-up, 10G-or-faster applicability test and had at least one parameter outside the project recommendation, therefore WARN.
- 10 hosts were SKIPPED because they were non-applicable or did not have enough evidence for a complete parameter evaluation.
- Applicability must be tied to an in-use physical NIC. Bond/bridge/other virtual interfaces must not by themselves make a host applicable.

### 4.3 Netstate

WARN hosts:

- BD-L2-SMCPAPP01NEW
- BD-L2-SMCPFIDO01NEW
- BD-L2-SMCPOIDCWAS01NEW
- BD-L2-SMCPOIDCWEB01NEW
- BD-L2-SMCPONM01NEW
- datacat-test

The other 53 hosts evaluated PASS for the independently validated NetworkManager/link-state logic. RX/TX error/drop counters remain display-only.

### 5.1 Multipath

Actual applicable hosts and map counts:

- haserpapp1: 2 maps
- haserpapp2: 2 maps
- haserpapq1: 2 maps
- haserpapq2: 2 maps
- haspoapp1: 2 maps
- haspoapp2: 2 maps

All six applicable hosts evaluated PASS for path redundancy in this validation. The remaining 53 hosts were SKIPPED because no real multipath map was detected.

## Interpretation rules

- SKIPPED is not a failure. It includes both non-applicable hosts and hosts with insufficient evidence, according to each rule.
- No FAIL status was produced in this selected validation set.
- The large WARN counts for Time Sync, Kdump, and 10G network parameters should be reviewed against the exact production parser output before they are used in customer-facing summaries.
- Final report distributions must come from the production batch runner after parser-path and applicability checks are locked.
