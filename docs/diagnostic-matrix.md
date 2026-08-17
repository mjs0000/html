# Diagnostic Mapping Matrix

## Active scope

The active automation/report scope is **22 items: System 18 + Network 3 + Storage 1**.

Excluded from the active diagnostic/report catalog:

- `SYS_BOOT_PARAM` — 부팅 파라미터
- `NET_10G` — 10G 환경 설정
- `STG_IO_SCHEDULER` — I/O Scheduler
- `STG_NFS_OPTIONS` — NFS Options

Diagnostic results use only `PASS`, `WARN`, `FAIL`, and `SKIPPED`. A/B/C grades are not used. Missing or insufficient evidence becomes `SKIPPED` and is omitted from customer-facing reports by default.

All 22 active diagnostics are eligible for HTML/DOCX/JSON rendering when applicable and when evidence is sufficient.

## Active mapping

| Sec | ID | Item | Key policy |
|---|---|---|---|
| 3.1 | `SYS_HW_CERT` | 하드웨어 인증 | Physical/VM split; Red Hat certification reference; no FAIL solely for lookup failure |
| 3.2 | `SYS_LIFECYCLE` | Life-Cycle | RHEL major version only; supported major PASS |
| 3.3 | `SYS_BOOT_MODE` | Boot Mode | UEFI PASS, BIOS WARN, unknown SKIPPED |
| 3.4 | `SYS_FILESYSTEM` | Filesystem | XFS + LVM only; non-XFS/non-LVM WARN; swap is reference only |
| 3.5 | `SYS_PACKAGE_UPDATE` | 주요 패키지 업데이트 | kernel only; compare by RHEL major + arch + kernel family |
| 3.6 | `SYS_SELINUX` | SELINUX | `getenforce` + `/etc/selinux/config` primary; `/proc/cmdline` supporting only |
| 3.7 | `SYS_FIREWALLD` | Firewalld | disabled + inactive PASS; enabled or active WARN |
| 3.8 | `SYS_TIME_SYNC` | 시간 동기화 | chronyd active + configured sources >= 4 PASS; selected source excluded |
| 3.9 | `SYS_KDUMP` | 덤프 수집(Kdump) | Kdump state and 5 explicit sysctl recommendations are separate sub-checks |
| 3.10 | `SYS_ERROR_LOG` | 시스템 에러 로그 | context-aware actionable log classification, not keyword-only |
| 3.11 | `SYS_KERNEL_PARAM` | 기본 커널 파라미터 | six project kernel parameters; per-parameter PASS/WARN/SKIPPED |
| 3.12 | `SYS_DEFAULT_SERVICE` | Default Service Enabled | only 12 unconditional-disable services; conditional services/default.target excluded |
| 3.13 | `SYS_APP_COREDUMP` | Application Core Dump | Core Limit, DefaultLimitCORE, Retention separate sub-checks |
| 3.14 | `SYS_LOGROTATE_SYSSTAT` | Logrotate / sysstat(SAR) | frequency daily/weekly, rotate >=12, SAR interval 1 minute |
| 3.15 | `SYS_TUNED` | Tuned | service + profile separate; Oracle profile excluded |
| 3.16 | `SYS_IRQBALANCE` | IRQ Balance Processing | service enabled/active + `IRQBALANCE_ONESHOT=yes` |
| 3.17 | `SYS_TIMER` | Timer | `dnf-makecache.timer` disabled/inactive recommended; SAR timer not duplicated |
| 3.18 | `SYS_OTHER_SETTINGS` | 기타 설정 | rsyslog systemd session/slice filter + empty cron MAILTO |
| 4.1 | `NET_BONDING` | 이중화(Bonding) | actual bond users only; all configured Slave links Up required for PASS |
| 4.2 | `NET_KERNEL_PARAM` | 네트워크 커널 파라미터 | only configured/in-use 10G+ NIC with link Up; seven project sysctls |
| 4.3 | `NET_NETSTATE` | Netstate | determine NetworkManager usage first; active/configured traffic links must be Up |
| 5.1 | `STG_MULTIPATH` | Device Mapper Multipath | actual multipath maps only; all paths usable and >=2 usable paths for PASS |

## Finalized policy details

### 3.5 Package Update

Only kernel is assessed. OpenSSL and OpenSSH are excluded. Minor release, EUS, ELC, and support stream are excluded from comparison. Preserve both running kernel and newest installed kernel. A newer installed kernel than the running kernel produces a WARN/reboot-required finding. If a trustworthy external reference cannot be obtained, use `SKIPPED` rather than inferring a failure.

### 3.6 SELinux

Primary evidence on all supported RHEL versions:

- runtime state from `getenforce` or `sestatus` fallback
- persistent state from `/etc/selinux/config`

`/proc/cmdline` and exact `selinux=0` are supporting evidence only. Runtime `Disabled` plus configured `disabled` is `PASS` whether or not `selinux=0` is present. Runtime/config mismatch is `WARN`. If one primary source is available, evaluation may proceed with a missing-source finding; if neither is available, `SKIPPED`.

### 3.8 Time Sync

Evaluate configured Chrony sources, not the currently selected source. `chronyd` active plus at least four configured time sources is `PASS`; fewer than four or inactive is `WARN`; indeterminate state is `SKIPPED`.

### 3.12 Default Service Enabled

Only these 12 services are assessed and expected disabled/inactive:

- `nis-domainname.service`
- `ostree-remount.service`
- `bluetooth.service`
- `cups.service`
- `atd.service`
- `wpa_supplicant.service`
- `avahi-daemon.service`
- `mdmonitor.service`
- `ModemManager.service`
- `rhsmcertd.service`
- `rtkit-daemon.service`
- `selinux-autorelabel-mark.service`

Conditional services and `default.target` are excluded from 3.12.

### 3.17 Timer

3.17 evaluates only `dnf-makecache.timer`. Disabled and inactive is `PASS`; enabled or active is `WARN`; insufficient evidence is `SKIPPED`. `sysstat-collect.timer` interval belongs only to 3.14.

### 4.1 Bonding

Evaluate only hosts with real bond interfaces. For redundancy state, inspect every configured Slave interface. PASS requires at least two Slave interfaces, Bond MII Up, and every Slave link/MII Up. Any Slave Down is `WARN`, even if the bond remains operational through another path.

### 4.2 Network Kernel Parameters

Applicability requires the same interface to satisfy all of the following:

1. physical NIC configured/in use
2. negotiated runtime speed >= 10000 Mbps
3. link/carrier Up

Only applicable hosts are evaluated against:

| Parameter | Recommended |
|---|---|
| `net.core.netdev_max_backlog` | `>= 2000` |
| `net.ipv4.tcp_rmem` | `4096 87380 16777216` exact |
| `net.ipv4.tcp_wmem` | `4096 16384 16777216` exact |
| `net.core.rmem_max` | `>= 16777216` |
| `net.core.wmem_max` | `>= 16777216` |
| `vm.min_free_kbytes` | `>= 1024000` |
| `net.core.netdev_budget` | `300` |

### 4.3 Netstate

First determine whether NetworkManager is actually managing interfaces. Missing `nmcli` alone is not a failure. If NetworkManager is in use, report active connection settings plus runtime link state. If it is not in use, report that fact and use `ip`/`ethtool` link evidence. Only interfaces that are active/configured and expected to carry traffic are evaluated for link Up/Down. RX/TX error/drop counters are display-only until a project threshold is defined.

### 5.1 Multipath

Evaluate only hosts with real multipath maps. Package installation or configuration-file presence alone does not make a host applicable. PASS requires an active/usable map, at least two usable paths, and no failed/down path. A map that remains operational after one path failure is still `WARN` because redundancy is degraded.

## Engine contract

1. Resolve candidate evidence.
2. Validate content; file presence alone is insufficient.
3. Parse into normalized facts.
4. Evaluate applicability before status.
5. Apply rules only to normalized facts.
6. Produce only `PASS`, `WARN`, `FAIL`, or `SKIPPED`.
7. Preserve evidence and remediation details.
8. Apply renderer inclusion after diagnosis.
9. Diagnosis is read-only.
10. HTML/DOCX/JSON consume the same common result model.
