# Diagnostic Mapping Matrix v4

## Active scope

The active automation/report scope is now **23 items: System 19 + Network 3 + Storage 1**.

Excluded from the active diagnostic/report catalog:

- `NET_10G` — 10G 환경 설정
- `STG_IO_SCHEDULER` — I/O Scheduler
- `STG_NFS_OPTIONS` — NFS Options

The original RockPLACE scope section numbers are retained as `source_section` in `spec/catalog.yaml` for traceability. Active report sections are renumbered after exclusions.

Customer-facing grades remain A/B/C only. Missing required evidence after candidate resolution is internal `SKIPPED` and is not rendered.

## Full active Mapping Matrix

| Active Sec | Source Sec | ID | Item | Automation | Parser | Preferred evidence | Normalized facts / applicability |
|---|---|---|---|---|---|---|---|
| 3.1 | 3.1 | `SYS_HW_CERT` | 하드웨어 인증 | Conditional | `hardware` | dmidecode, lscpu, lspci | vendor/model/CPU/PCI; certification requires Red Hat/internal reference |
| 3.2 | 3.2 | `SYS_LIFECYCLE` | Life-Cycle | Conditional | `lifecycle` | redhat-release, os-release, uname | RHEL version/kernel; lifecycle dates require versioned reference |
| 3.3 | 3.3 | `SYS_BOOT_MODE` | Boot Mode | Full | `boot_mode` | firmware listing variants, validated efibootmgr, /boot/efi, mokutil | boot mode/confidence/EFI entries; command-error output is not positive evidence |
| 3.4 | 3.4 | `SYS_FILESYSTEM` | Filesystem | Full | `filesystem` | findmnt, lsblk, df variants, fstab, LVM, swap | mount/fstype/use%/inode/LVM/swap |
| 3.5 | 3.5 | `SYS_PACKAGE_UPDATE` | 주요 패키지 업데이트 | Conditional | `packages` | installed-rpms, dnf list, optional updateinfo | installed NEVRA/kernel; latest/security status may need external advisory data |
| 3.6 | 3.6 | `SYS_SELINUX` | SELINUX | Full | `selinux` | sestatus/getenforce/config | runtime/config mode |
| 3.7 | 3.7 | `SYS_FIREWALLD` | Firewalld | Conditional | `firewalld` | systemd, firewall-cmd, firewalld config | installed/active/enabled/zones/services/ports; desired state depends on customer policy |
| 3.8 | 3.8 | `SYS_TIME_SYNC` | 시간 동기화 | Full | `chrony` | sources/tracking/sourcestats/chrony.conf/timedatectl | configured/reachable/selected source, offset, stratum, sync/timezone |
| 3.9 | 3.9 | `SYS_KDUMP` | 덤프 수집 | Full | `kdump` | systemd, cmdline, kexec_crash_size, kdump.conf, sysctl, optional kdumpctl | enabled/active/crashkernel/reserved memory/target/panic sysctls |
| 3.10 | 3.10 | `SYS_ERROR_LOG` | 시스템 에러 로그 | **Conditional** | `error_log` | `/var/log/messages*`, **dmesg**, journal | source/timestamp/category/severity/component/pattern/message/count; keyword match requires context/severity assessment |
| 3.11 | 3.11 | `SYS_KERNEL_PARAM` | 기본 커널 파라미터 | Full | `sysctl` | sysctl -a, proc/sys | dirty ratios/swappiness/ip_forward/somaxconn/syn backlog |
| 3.12 | 3.12 | `SYS_BOOT_PARAM` | 부팅 파라미터 | Full | `boot_parameters` | proc/cmdline, grub | normalized kernel command-line tokens |
| 3.13 | 3.13 | `SYS_DEFAULT_SERVICE` | Default Service Enabled | Conditional | `services` | systemd unit-files/units | installed/enabled/active/masked + feature applicability |
| 3.14 | 3.14 | `SYS_APP_COREDUMP` | Application Core Dump | Full | `coredump` | limits, coredump.conf, core_pattern, tmpfiles | core limit/pattern/storage/retention |
| 3.15 | 3.15 | `SYS_LOGROTATE_SYSSTAT` | Logrotate / sysstat(SAR) | Full + applicability | `logrotate_sysstat` | logrotate config/debug, package/timer/cron | rotation cadence/retention; sysstat installed/enabled/interval |
| 3.16 | 3.16 | `SYS_TUNED` | Tuned | Conditional | `tuned` | tuned-adm, profile, systemd, workload/NIC facts | daemon/profile/VM-BM/workload context |
| 3.17 | 3.17 | `SYS_IRQBALANCE` | IRQ Balance Processing | Full | `irqbalance` | irqbalance config + systemd | enabled/active/ONESHOT |
| 3.18 | 3.18 | `SYS_TIMER` | Timer | Full | `systemd_timer` | list-timers, timer units | timer enabled/active/next/last run |
| 3.19 | 3.19 | `SYS_OTHER_SETTINGS` | 기타 설정 | Conditional | `other_settings` | profile, rsyslog, cron sources | history/session-filter/MAILTO; customer policy dependent |
| 4.1 | 4.1 | `NET_BONDING` | 이중화 (Bonding) | Conditional | `bonding` | proc/*/net/bonding, NM profile/nmcli fallback, ip link | mode/miimon/LACP/slaves/active/link; only bonding users |
| 4.2 | 4.3 | `NET_KERNEL_PARAM` | 네트워크 커널 파라미터 | Conditional | `network_sysctl` | **ethtool speed first**, sysctl, softnet_stat, ethtool/IP counters | **applicable only when >=10Gbps physical NIC detected**; otherwise SKIPPED |
| 4.3 | 4.4 | `NET_NETSTATE` | Netstate | Full | `netstate` | nmcli if present; ip/ethtool/NM config+journal fallback | carrier/speed/device/error/drop/NM state |
| 5.1 | 5.2 | `STG_MULTIPATH` | Device Mapper Multipath | Conditional | `multipath` | multipath -ll, multipathd config, multipath.conf, FC/DM context | applicable/driver/maps/WWID/vendor/model/path state/policy; only multipath clients |

## System error log policy

`SYS_ERROR_LOG` is explicitly **Conditional**. The parser searches multiple log sources and returns structured findings; the rule engine decides whether findings are benign, require review, or indicate a serious problem.

### Sources

Ordered candidates include:

- `var/log/messages`
- `var/log/messages-*`
- `sos_commands/kernel/dmesg*`
- `sos_commands/logs/dmesg*`
- collected `journalctl*`

### Search profile

The scope-style search intent is represented in policy/mapping rather than invoking shell `egrep` directly. The initial keyword set includes:

```text
blk_update_request: I/O error
rejecting I/O to offline device
killing request
hostbyte=DID_NO_CONNECT
mark as failed
remaining active paths
parity
Abort command issued
Hardware Error
error
emerg
alert
aleart
crit
err
warn
fail
```

The implementation should provide equivalent behavior to a scan such as:

```text
egrep -w '(blk_update_request: I/O error|rejecting I/O to offline device|killing request|hostbyte=DID_NO_CONNECT|mark as failed|remaining active paths|parity|Abort command issued|Hardware Error|error|emerg|aleart|crit|err|warn|fail)'
```

but execute the matching in Python so that each hit retains `source`, `timestamp`, `matched_pattern`, `component`, `severity`, full message and occurrence count.

### Conditional grading principle

A keyword hit is **not automatically C**. For example, documentation text, historical/recovered events, benign driver messages or unrelated words containing generic `error/warn/fail` may be false positives. The rule layer must be able to classify findings by pattern family and context. Storage/I/O path failures and Hardware Error events should have higher severity than generic warning matches.

## Network policy after removing standalone 10G item

There is no longer a separate `10G 환경 설정` report item. NIC speed is now a fact used by `NET_KERNEL_PARAM` applicability:

```text
ethtool / link evidence
        ↓
physical NIC speed >= 10000 Mbps ?
        ├─ No  → NET_KERNEL_PARAM = SKIPPED (not rendered)
        └─ Yes → parse sysctl + softnet + NIC counters
                     ↓
                 apply network parameter rules
```

This keeps the scope focused while ensuring the 10G-specific kernel tuning recommendations are not incorrectly applied to 1G environments.

## Storage policy after scope reduction

Storage report scope now contains only `Device Mapper Multipath`. I/O Scheduler and NFS Options are removed from the active catalog and mapping rules. Block/LVM evidence may remain as supporting context for Multipath parsing, but they are not independent report items.

## Engine contract

1. Resolve evidence through ordered candidate paths/globs.
2. Validate command output content; file existence alone is not a fact.
3. Parser emits normalized facts/findings only.
4. Applicability runs before A/B/C grading.
5. Conditional items use environment/context and finding severity.
6. Missing required evidence becomes internal `SKIPPED`.
7. Customer-facing output renders only A/B/C reportable results.
8. HTML and DOCX use the same result model.
