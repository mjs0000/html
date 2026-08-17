# 59-host corpus status validation

This document records independent, single-pass validation evidence against the current 59-sosreport corpus.

## Scope and method

- Corpus size: 59 sosreport archives.
- Processing errors: 0 in the recorded independent scans.
- Validation was performed by streaming each tar.xz once and extracting only the evidence required by the selected rules.
- Status vocabulary is limited to PASS, WARN, FAIL, and SKIPPED.
- These figures are corpus validation evidence. They must not replace the production `sosdiag` runner when final customer-facing reports are generated.

## Selected diagnostic distribution

The system/storage figures below come from the earlier independent scan. The network figures for 4.2 and 4.3 were revalidated later after tightening physical-NIC applicability and excluding non-reportable virtual links.

| Diagnostic | PASS | WARN | FAIL | SKIPPED |
|---|---:|---:|---:|---:|
| SYS_SELINUX (3.6) | 55 | 4 | 0 | 0 |
| SYS_TIME_SYNC (3.8) | 0 | 54 | 0 | 5 |
| SYS_KDUMP (3.9) | 24 | 35 | 0 | 0 |
| NET_BONDING (4.1) | 33 | 0 | 0 | 26 |
| NET_KERNEL_PARAM (4.2), revalidated | 0 | 54 | 0 | 5 |
| NET_NETSTATE (4.3), revalidated | 59 | 0 | 0 | 0 |
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

- 24 hosts evaluated PASS under the earlier Kdump validation logic.
- 35 hosts evaluated WARN in that earlier scan.
- Production Kdump semantics were tightened after this scan, so these figures must not be presented as current production output.

### 4.1 Bonding

- 33 hosts contain actual Bonding evidence and evaluated PASS in the independent validation.
- 26 hosts have no Bonding configuration and are therefore SKIPPED/non-applicable.
- The real corpus commonly stores Bonding data under `proc/<pid>/net/bonding/*`; the parser must support this path family.

### 4.2 Network Kernel Parameters — revalidated

A dedicated 59-host network revalidation was executed after the applicability rule was tightened. The scan completed all 59 archives with no processing errors.

- 54 hosts have at least one configured/in-use, link-up physical Ethernet interface negotiated at 10G or faster and evaluated WARN because one or more project network sysctl recommendations were not met.
- 5 hosts are SKIPPED because no qualifying in-use 10G+ physical Ethernet interface was established.
- The five SKIPPED hosts are `FDID-GW-TS`, `FDID-NODE-TS1`, `FDID-NODE-TS2`, `FDID-NODE-TS3`, and `datacat-test`.
- Bond, bridge, virbr, and other virtual interfaces do not by themselves make a host applicable.
- Physical bond slaves may qualify when the underlying Ethernet device itself is active/configured, link-up, and 10G+.

This supersedes the earlier independent figure of WARN 49 / SKIPPED 10.

#### 4.2 warning cause distribution

For all 54 applicable hosts, the following six parameters were below or different from the project recommendation in the independent revalidation:

| Parameter | WARN hosts |
|---|---:|
| `net.core.netdev_max_backlog` | 54 |
| `net.ipv4.tcp_rmem` | 54 |
| `net.ipv4.tcp_wmem` | 54 |
| `net.core.rmem_max` | 54 |
| `net.core.wmem_max` | 54 |
| `vm.min_free_kbytes` | 54 |

`net.core.netdev_budget=300` satisfied the project recommendation on all 54 applicable hosts in this independent validation and therefore did not contribute to the WARN result.

The production batch report now aggregates structured sub-status values so repeated Host-level warnings can be summarized by parameter and affected Host count instead of printing the same finding dozens of times in the report overview.

### 4.3 Netstate — revalidated

The same 59-host network revalidation applied the locked Netstate policy:

- evaluate NetworkManager only when it is actually in use,
- evaluate only configured/in-use links,
- do not warn on unused disconnected ports,
- exclude local virtual bridge devices such as `virbr0` from physical-link health findings,
- use `ip` address/route/link evidence when `nmcli` evidence is unavailable.

Result: all 59 hosts evaluated PASS in the independent revalidation.

The six WARN hosts from the earlier scan (`BD-L2-SMCPAPP01NEW`, `BD-L2-SMCPFIDO01NEW`, `BD-L2-SMCPOIDCWAS01NEW`, `BD-L2-SMCPOIDCWEB01NEW`, `BD-L2-SMCPONM01NEW`, and `datacat-test`) were artifacts of including non-reportable virtual/local links or overly broad fallback behavior. The earlier 53 PASS / 6 WARN distribution is superseded.

RX/TX error/drop counters remain display-only.

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
- The network revalidation is still an independent corpus scan, not a production `sosdiag analyze-corpus` execution.
- Final customer-report distributions must come from the production batch runner after the complete repository is executable against the corpus.
