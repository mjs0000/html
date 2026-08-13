# Diagnostic Mapping Matrix v5

## Active scope

The active automation/report scope is **23 items: System 19 + Network 3 + Storage 1**.

Excluded from the active diagnostic/report catalog:

- `NET_10G` — 10G 환경 설정
- `STG_IO_SCHEDULER` — I/O Scheduler
- `STG_NFS_OPTIONS` — NFS Options

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
| 3.10 | 3.10 | `SYS_ERROR_LOG` | 시스템 에러 로그 | Conditional | `error_log` | `/var/log/messages*`, dmesg, journal | source/timestamp/category/severity/component/pattern/message/count; keyword hit requires context/severity assessment |
| 3.11 | 3.11 | `SYS_KERNEL_PARAM` | 기본 커널 파라미터 | Full | `sysctl` | sysctl -a, proc/sys | dirty ratios/swappiness/ip_forward/somaxconn/syn backlog |
| 3.12 | 3.12 | `SYS_BOOT_PARAM` | 부팅 파라미터 | Full / policy pending | `boot_parameters` | `/proc/cmdline`, `/etc/default/grub`, grub.cfg | runtime tokens, persistent tokens, token-value map, runtime/persistent diff; exact A/B/C token policy not yet defined in Scope body |
| 3.13 | 3.13 | `SYS_DEFAULT_SERVICE` | Default Service Enabled | Conditional | `services` | systemd unit-files/units | installed/enabled/active/masked + feature applicability |
| 3.14 | 3.14 | `SYS_APP_COREDUMP` | Application Core Dump | Full | `coredump` | limits, coredump.conf, `/etc/systemd/system.conf`, core_pattern, `/usr/lib/tmpfiles.d/systemd.conf`, tmpfiles overrides | core limits, `DefaultLimitCORE`, core pattern/storage, retention/exclusion |
| 3.15 | 3.15 | `SYS_LOGROTATE_SYSSTAT` | Logrotate / sysstat(SAR) | Full | `logrotate_sysstat` | logrotate config/debug, installed-rpms, `/usr/lib/systemd/system/sysstat-collect.timer`, timer overrides/list-timers | rotation cadence/retention; sysstat installed/timer/OnCalendar/enabled |
| 3.16 | 3.16 | `SYS_TUNED` | Tuned | Conditional | `tuned` | tuned-adm, profile, systemd, workload/NIC facts | daemon/profile/VM-BM/workload context |
| 3.17 | 3.17 | `SYS_IRQBALANCE` | IRQ Balance Processing | Full | `irqbalance` | irqbalance config + systemd | enabled/active/ONESHOT |
| 3.18 | 3.18 | `SYS_TIMER` | Timer | Conditional | `systemd_timer` | `systemctl list-timers --all`, unit files | inventory first; evaluate only timers with explicit policy, including dnf-makecache.timer |
| 3.19 | 3.19 | `SYS_OTHER_SETTINGS` | 기타 설정 (rsyslog / cron) | Full | `other_settings` | `/etc/rsyslog.d/0-ignore-systemd-session-slice.conf`, `/etc/crontab` | rsyslog filter presence/content + cron MAILTO only |
| 4.1 | 4.1 | `NET_BONDING` | 이중화 (Bonding) | Conditional | `bonding` | proc/*/net/bonding, NM profile/nmcli fallback, ip link | mode/miimon/LACP/slaves/active/link; only bonding users |
| 4.2 | 4.3 | `NET_KERNEL_PARAM` | 네트워크 커널 파라미터 | Conditional | `network_sysctl` | physical NIC ethtool speed + link/carrier first, sysctl, softnet_stat, ethtool/IP counters | applicable only when an actually connected physical NIC is operating at >=10Gbps; otherwise SKIPPED |
| 4.3 | 4.4 | `NET_NETSTATE` | Netstate | Full | `netstate` | nmcli if present; ip/ethtool/NM config+journal fallback | carrier/speed/device/error/drop/NM state |
| 5.1 | 5.2 | `STG_MULTIPATH` | Device Mapper Multipath | Conditional | `multipath` | multipath -ll, multipathd config, multipath.conf, FC/DM context | applicable/driver/maps/WWID/vendor/model/path state/policy; only multipath clients |

## 3.12 Boot Parameters — current meaning

The source Scope table of contents includes **3.12 부팅 파라미터**, but the corresponding body does not provide a dedicated detailed rule table or explicit required/prohibited token list. Therefore the automation must not invent an A/B/C policy.

The current parser responsibility is:

1. Read runtime kernel command line from `/proc/cmdline`.
2. Read persistent GRUB configuration from `/etc/default/grub`, `/boot/grub2/grub.cfg`, and EFI grub.cfg candidates.
3. Normalize command-line tokens into key/value facts.
4. Compare runtime tokens with persistent GRUB tokens and retain differences.
5. Expose well-known values such as `crashkernel` to other diagnostics where needed, but do not duplicate Kdump grading in 3.12.
6. Keep the exact 3.12 A/B/C token policy as `pending_policy` until RockPLACE defines which boot parameters are mandatory, prohibited, or contextual.

Example normalized facts:

```yaml
runtime_cmdline_tokens:
  - ro
  - crashkernel=1G-4G:192M,4G-64G:256M,64G-:512M
  - rd.lvm.lv=rhel/root
persistent_grub_tokens:
  - ro
  - crashkernel=auto
runtime_vs_persistent_diff:
  - crashkernel
```

## 3.14 Application Core Dump

The diagnostic now explicitly checks both files requested by policy:

- `/etc/systemd/system.conf`
  - inspect `DefaultLimitCORE`
  - recommended value: `infinity`
- `/usr/lib/tmpfiles.d/systemd.conf`
  - inspect `/var/lib/systemd/coredump` retention definition
  - Scope example shows default `3d`; review exclusion or longer retention such as `15d` when required

Other evidence remains `limits.conf/limits.d`, `coredump.conf`, `core_pattern` and `/etc/tmpfiles.d/*` overrides.

The Scope explicitly recommends unlimited soft/hard core values, shows `DefaultLimitCORE=infinity`, and describes `/var/lib/systemd/coredump` retention controlled by tmpfiles. The report should distinguish core-capture capability from retention policy.

## 3.15 Logrotate / sysstat(SAR)

The sysstat part must explicitly inspect:

```text
/usr/lib/systemd/system/sysstat-collect.timer
```

The parser extracts `OnCalendar` and effective timer state. The Scope example shows a 10-minute default (`*:00/10`) and recommends changing the SAR collection interval to 1 minute. Effective overrides under `/etc/systemd/system/sysstat-collect.timer.d/*` must take precedence over the vendor unit when present.

Normalized facts include:

```yaml
sysstat_installed: true|false
sysstat_timer_present: true|false
sysstat_timer_oncalendar: "*:00/1"
sysstat_timer_enabled: true|false
```

## 3.18 Timer — Conditional

`SYS_TIMER` is now **Conditional**.

Processing order:

```text
systemctl list-timers --all
        ↓
Inventory timers
        ↓
Does timer have an explicit diagnostic policy?
        ├─ No  → inventory/context only; no finding
        └─ Yes → evaluate the timer-specific rule
```

A known Scope rule is `dnf-makecache.timer`, which the Scope recommends disabling because it periodically creates DNF cache and log activity. Other timers are not automatically considered problematic merely because they exist.

## 3.19 Other Settings — only rsyslog and cron

`SYS_OTHER_SETTINGS` is now **Full** and contains only two subchecks. The previous history/profile subcheck is removed from the active mapping.

### rsyslog

Required file:

```text
/etc/rsyslog.d/0-ignore-systemd-session-slice.conf
```

If absent, the remediation instructs creation of the file and insertion of the configured systemd session-slice filtering rules. The mapping stores the required content as structured expected-content lines rather than executing changes during diagnosis.

Required filtering intent:

```text
if $programname == "systemd" and ($msg contains "User Manager for UID"
  or $msg contains "user@"
  or $msg contains "run-user-"
  or $msg contains "user-runtime-dir@"
  or $msg contains "slice User Slice of UID"
  or $msg contains "User runtime directory /run/user/") then stop

if ($programname == "systemd" and $procid != "1") and
  ($msg contains "slice User Application Slice"
  or $msg contains "Queued start job for default target Main User Target"
  or $msg contains "Mark boot as successful after the user"
  or $msg contains "Daily Cleanup of User's Temporary Directories"
  or $msg contains "D-Bus User Message Bus Socket"
  or $msg contains "Create User's Volatile Files and Directories"
  or $msg contains "Exit the Session"
  or $msg contains "Reached target"
  or $msg contains "Stopped target"
  or $msg contains "Startup finished in") then stop
```

After an administrator applies the remediation, restart rsyslog with:

```text
systemctl restart rsyslog
```

The diagnostic/report generator itself does **not** modify the customer host; it only reports the required remediation.

### cron

Required file:

```text
/etc/crontab
```

Expected setting:

```text
MAILTO=""
```

If the current value is `MAILTO="root"`, remediation is to change it to `MAILTO=""` so cron output is not mailed to the local root mailbox.

## System error log policy

`SYS_ERROR_LOG` is Conditional. Sources include `/var/log/messages*`, dmesg and collected journal output. Keyword matches are classified by pattern family and context; a generic `warn/error/fail` match is not automatically grade C.

## Network 10G applicability

There is no standalone 10G report item. `NET_KERNEL_PARAM` runs only when at least one **physical** NIC is actually connected and operating at >=10Gbps. Installed/capable but disconnected NICs, `Link detected: no`, `NO-CARRIER`, or DOWN interfaces do not qualify. For bonding, physical slave link state is evaluated rather than logical bond speed alone.

## Storage scope

Storage report scope contains only Device Mapper Multipath. I/O Scheduler and NFS Options remain excluded.

## Engine contract

1. Resolve evidence through ordered candidate paths/globs.
2. Validate command output content; file existence alone is not a fact.
3. Parser emits normalized facts/findings only.
4. Applicability runs before A/B/C grading.
5. Conditional items use environment/context and explicit sub-rules.
6. Missing required evidence becomes internal `SKIPPED`.
7. Customer-facing output renders only A/B/C reportable results.
8. Diagnosis is read-only; remediation commands/configuration are report guidance and are never executed against the customer system by the analyzer.
9. HTML and DOCX use the same result model.
