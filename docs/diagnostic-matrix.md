# Diagnostic Mapping Matrix v7

## Active scope

The active automation/report scope is **22 items: System 18 + Network 3 + Storage 1**.

Excluded from the active diagnostic/report catalog:

- `SYS_BOOT_PARAM` — 부팅 파라미터
- `NET_10G` — 10G 환경 설정
- `STG_IO_SCHEDULER` — I/O Scheduler
- `STG_NFS_OPTIONS` — NFS Options

The original RockPLACE scope section numbers are retained as `source_section` in `spec/catalog.yaml` for traceability. Active report sections are renumbered after exclusions.

Customer-facing grades remain A/B/C only. Missing required evidence after candidate resolution is internal `SKIPPED` and is not rendered.

## Output-specific rendering policy

HTML intentionally excludes these three diagnostics even though they remain active for DOCX/JSON processing:

- `3.1 SYS_HW_CERT` — 하드웨어 인증
- `3.2 SYS_LIFECYCLE` — Life-Cycle
- `3.5 SYS_PACKAGE_UPDATE` — 주요 패키지 업데이트

Therefore HTML renders 19 of the 22 active diagnostics at most, subject to applicability/SKIPPED filtering. DOCX and JSON retain the 22-item active catalog unless an item is SKIPPED or another renderer policy excludes it.

## Full active Mapping Matrix

| Active Sec | Source Sec | ID | Item | Automation | HTML | Preferred evidence | Normalized facts / applicability |
|---|---|---|---|---|---|---|---|
| 3.1 | 3.1 | `SYS_HW_CERT` | 하드웨어 인증 | Conditional | Excluded | dmidecode, lscpu, lspci | certification requires Red Hat/internal reference |
| 3.2 | 3.2 | `SYS_LIFECYCLE` | Life-Cycle | Conditional | Excluded | redhat-release, os-release, uname | lifecycle requires versioned reference |
| 3.3 | 3.3 | `SYS_BOOT_MODE` | Boot Mode | Full | Included | firmware listing, validated efibootmgr, /boot/efi, mokutil | boot mode/confidence/EFI evidence |
| 3.4 | 3.4 | `SYS_FILESYSTEM` | Filesystem | Full | Included | findmnt, lsblk, df, fstab, LVM, swap | mount/fstype/use%/inode/LVM/swap |
| 3.5 | 3.5 | `SYS_PACKAGE_UPDATE` | 주요 패키지 업데이트 | Conditional | Excluded | installed-rpms, dnf, optional updateinfo | only kernel, openssl, openssh |
| 3.6 | 3.6 | `SYS_SELINUX` | SELINUX | Full | Included | sestatus/getenforce/config | recommended disabled; display actual state |
| 3.7 | 3.7 | `SYS_FIREWALLD` | Firewalld | Conditional | Included | systemd, firewall-cmd, config | recommended disabled; display actual state/config |
| 3.8 | 3.8 | `SYS_TIME_SYNC` | 시간 동기화 | Full | Included | chrony sources/tracking/config/timedatectl | configured/usable/selected/sync/timezone |
| 3.9 | 3.9 | `SYS_KDUMP` | 덤프 수집 | Full | Included | systemd, cmdline, kexec_crash_size, kdump.conf, sysctl | service/crashkernel/reserved memory/target/panic |
| 3.10 | 3.10 | `SYS_ERROR_LOG` | 시스템 에러 로그 | Conditional | Included | messages, dmesg, journal | classified findings; generic keyword != automatic C |
| 3.11 | 3.11 | `SYS_KERNEL_PARAM` | 기본 커널 파라미터 | Full | Included | sysctl, proc/sys | base kernel policy |
| 3.12 | 3.13 | `SYS_DEFAULT_SERVICE` | Default Service Enabled | Conditional | Included | systemd units | service state + feature applicability |
| 3.13 | 3.14 | `SYS_APP_COREDUMP` | Application Core Dump | Full | Included | limits, coredump, system.conf, tmpfiles | limits/storage/retention |
| 3.14 | 3.15 | `SYS_LOGROTATE_SYSSTAT` | Logrotate / sysstat(SAR) | Full | Included | logrotate, sysstat-collect.timer | rotation + effective SAR interval |
| 3.15 | 3.16 | `SYS_TUNED` | Tuned | Conditional | Included | tuned-adm, profile, systemd | context-dependent profile |
| 3.16 | 3.17 | `SYS_IRQBALANCE` | IRQ Balance Processing | Full | Included | irqbalance config + systemd | active/enabled/ONESHOT |
| 3.17 | 3.18 | `SYS_TIMER` | Timer | Conditional | Included | list-timers, timer units | evaluate only explicit timer policies |
| 3.18 | 3.19 | `SYS_OTHER_SETTINGS` | 기타 설정 (rsyslog / cron) | Full | Included | specific rsyslog filter + /etc/crontab | filter + MAILTO only |
| 4.1 | 4.1 | `NET_BONDING` | 이중화 (Bonding) | Conditional | Included | proc bonding, NM, ip | only actual bonding users |
| 4.2 | 4.3 | `NET_KERNEL_PARAM` | 네트워크 커널 파라미터 | Conditional | Included | active physical 10G+ link, sysctl, softnet | only connected 10G+ physical NIC |
| 4.3 | 4.4 | `NET_NETSTATE` | Netstate | Full | Included | NetworkManager/nmcli/profile + ip/ethtool | NM use status; if used, report settings |
| 5.1 | 5.2 | `STG_MULTIPATH` | Device Mapper Multipath | Conditional | Included | multipath, multipathd, FC/DM | only actual multipath clients |

## Detailed policy changes

### 3.5 Package Updates

Only three package groups are assessed:

- `kernel`
- `openssl`
- `openssh`

The parser may inspect all installed RPM rows internally to locate package-family members, but only these groups become normalized/reportable package-update facts. Installed NEVRA/version is retained. Latest/security status may still require an advisory/reference provider. This item is excluded from HTML but remains available for DOCX/JSON.

### 3.6 SELINUX

RockPLACE recommended state is `disabled`.

The report always displays detected state:

- runtime mode from `getenforce`/`sestatus`
- configured mode from `/etc/selinux/config`
- mismatch if runtime and persistent configuration differ

`Disabled` is the recommended state. `Permissive` and `Enforcing` remain visible as current-state evidence rather than being hidden.

### 3.7 Firewalld

RockPLACE recommended state is `disabled`.

The parser displays:

- installed
- enabled
- active
- default zone
- collected zones/services/ports/rich rules when Firewalld is active

If enabled/active, the current state/configuration must still be displayed. The recommendation remains disabled.

### 4.2 Network Kernel Parameters — only active connected 10G+

Applicability requires all of the following:

1. Physical NIC
2. Actual runtime speed >= 10000 Mbps
3. `Link detected: yes`
4. Carrier up / operationally connected

A 10G-capable but disconnected NIC does not qualify. For bonding, physical slave NIC links determine applicability.

When applicable, evaluate exactly this policy table:

| Parameter | Default | Recommended | Operator |
|---|---:|---:|---|
| `net.core.netdev_max_backlog` | 1000 | >= 2000 | gte |
| `net.ipv4.tcp_rmem` | 4096 131072 6291456 | 4096 87380 16777216 | exact triplet |
| `net.ipv4.tcp_wmem` | 4096 16384 4194304 | 4096 16384 16777216 | exact triplet |
| `net.core.rmem_max` | 212992 | 16777216 | gte |
| `net.core.wmem_max` | 212992 | 16777216 | gte |
| `vm.min_free_kbytes` | system calculated | >= 1024000 | gte |
| `net.core.netdev_budget` | 300 | 300 | eq |

`net.core.netdev_max_backlog` represents the packet backlog used when packets arrive faster than the kernel can process them; values above 10000 are not considered useful by this policy. `vm.min_free_kbytes` is reviewed as reserved kernel memory, with at least roughly 1GiB represented by the configured threshold for the applicable large/multi-interface 10G environment.

### 4.3 Netstate — NetworkManager usage and settings

The first question is whether NetworkManager is actually being used.

Normalize and display:

- NetworkManager installed/enabled/active
- whether it is actually managing interfaces
- whether nmcli evidence is available

If NetworkManager is in use, inspect and report collected configuration such as:

- active connection/profile name
- interface
- connection type
- IPv4 method/address/gateway/DNS
- IPv6 method
- MTU
- autoconnect
- current carrier/operstate/speed
- RX/TX error/drop counters

Preferred evidence is nmcli plus `/etc/NetworkManager/system-connections/*`. If nmcli output is absent, NetworkManager profile/config plus `ip`/`ethtool` are valid fallbacks. Missing nmcli alone is not a failure.

If NetworkManager is not in use, report that fact and show current link information from `ip`/`ethtool`; do not fabricate NetworkManager configuration values.

## Engine contract

1. Resolve candidate evidence.
2. Validate content; file presence alone is insufficient.
3. Parse into normalized facts.
4. Evaluate applicability before grading.
5. Apply rules only to normalized facts.
6. Produce PASS/WARN/FAIL/SKIPPED and customer A/B/C where reportable.
7. Apply renderer-specific inclusion after diagnosis; HTML exclusion does not remove a diagnostic from the common result model.
8. Preserve evidence and remediation.
9. Diagnosis is read-only.
10. HTML/DOCX/JSON share the common result model, with renderer-specific visibility policy layered on top.
