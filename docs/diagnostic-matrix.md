# Diagnostic Mapping Matrix v6

## Active scope

The active automation/report scope is **22 items: System 18 + Network 3 + Storage 1**.

Excluded from the active diagnostic/report catalog:

- `SYS_BOOT_PARAM` — 부팅 파라미터
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
| 3.10 | 3.10 | `SYS_ERROR_LOG` | 시스템 에러 로그 | Conditional | `error_log` | `/var/log/messages*`, dmesg, journal | source/timestamp/category/severity/component/pattern/message/count; keyword hit requires context/severity assessment |
| 3.11 | 3.11 | `SYS_KERNEL_PARAM` | 기본 커널 파라미터 | Full | `sysctl` | sysctl -a, proc/sys | dirty ratios/swappiness/ip_forward/somaxconn/syn backlog |
| 3.12 | 3.13 | `SYS_DEFAULT_SERVICE` | Default Service Enabled | Conditional | `services` | systemd unit-files/units | installed/enabled/active/masked + feature applicability |
| 3.13 | 3.14 | `SYS_APP_COREDUMP` | Application Core Dump | Full | `coredump` | limits, coredump.conf, `/etc/systemd/system.conf`, core_pattern, `/usr/lib/tmpfiles.d/systemd.conf`, tmpfiles overrides | core limits, `DefaultLimitCORE`, core pattern/storage, retention/exclusion |
| 3.14 | 3.15 | `SYS_LOGROTATE_SYSSTAT` | Logrotate / sysstat(SAR) | Full | `logrotate_sysstat` | logrotate config/debug, installed-rpms, `/usr/lib/systemd/system/sysstat-collect.timer`, timer overrides/list-timers | rotation cadence/retention; sysstat installed/timer/OnCalendar/enabled |
| 3.15 | 3.16 | `SYS_TUNED` | Tuned | Conditional | `tuned` | tuned-adm, profile, systemd, workload/NIC facts | daemon/profile/VM-BM/workload context |
| 3.16 | 3.17 | `SYS_IRQBALANCE` | IRQ Balance Processing | Full | `irqbalance` | irqbalance config + systemd | enabled/active/ONESHOT |
| 3.17 | 3.18 | `SYS_TIMER` | Timer | Conditional | `systemd_timer` | `systemctl list-timers --all`, unit files | inventory first; evaluate only timers with explicit policy, including dnf-makecache.timer |
| 3.18 | 3.19 | `SYS_OTHER_SETTINGS` | 기타 설정 (rsyslog / cron) | Full | `other_settings` | `/etc/rsyslog.d/0-ignore-systemd-session-slice.conf`, `/etc/crontab` | rsyslog filter presence/content + cron MAILTO only |
| 4.1 | 4.1 | `NET_BONDING` | 이중화 (Bonding) | Conditional | `bonding` | proc/*/net/bonding, NM profile/nmcli fallback, ip link | mode/miimon/LACP/slaves/active/link; only bonding users |
| 4.2 | 4.3 | `NET_KERNEL_PARAM` | 네트워크 커널 파라미터 | Conditional | `network_sysctl` | physical NIC ethtool speed + link/carrier first, sysctl, softnet_stat, ethtool/IP counters | applicable only when an actually connected physical NIC is operating at >=10Gbps; otherwise SKIPPED |
| 4.3 | 4.4 | `NET_NETSTATE` | Netstate | Full | `netstate` | nmcli if present; ip/ethtool/NM config+journal fallback | carrier/speed/device/error/drop/NM state |
| 5.1 | 5.2 | `STG_MULTIPATH` | Device Mapper Multipath | Conditional | `multipath` | multipath -ll, multipathd config, multipath.conf, FC/DM context | applicable/driver/maps/WWID/vendor/model/path state/policy; only multipath clients |

## Detailed processing contract

Every diagnostic follows the same execution stages where applicable:

1. Resolve ordered candidate files/globs from the extracted sosreport.
2. Validate the command/file content. File presence alone is never a positive fact.
3. Parse raw text into typed normalized facts.
4. Evaluate applicability before grading.
5. Apply the diagnostic rule to normalized facts only; the rule engine does not parse raw text.
6. Produce internal status `PASS/WARN/FAIL/SKIPPED` and customer grade A/B/C for reportable items.
7. Preserve exact evidence source paths and important matched text/values.
8. Render the same result model to HTML/DOCX/JSON.

## Item processing details

### 3.1 Hardware Certification

Parse manufacturer/model/CPU/PCI/NIC facts from `dmidecode`, `lscpu`, and `lspci`. Hardware certification itself is not inferred locally; normalized hardware identifiers are passed to a Red Hat/internal certification reference provider. Missing authoritative certification data must not be converted to C.

### 3.2 Life-Cycle

Parse RHEL major/minor and kernel from `redhat-release`, `os-release`, and uname. Compare against a versioned lifecycle reference provider. Support end dates, EUS/ELS status, and current supported minor status are external-reference facts rather than sosreport facts.

### 3.3 Boot Mode

Use validated `efibootmgr` output, firmware directory listings, `/boot/efi` supporting evidence, and optional Secure Boot state. Reject shell-error output as evidence. Normalize `boot_mode`, EFI runtime presence, EFI mount presence, command success, and confidence. Existing production Legacy BIOS is not automatically C solely because new installations prefer UEFI.

### 3.4 Filesystem

Read `findmnt`, `lsblk`, supported `df` variants, fstab, LVM and swap. Normalize mount/source/fstype/usage/inode, LVM relationships, and swap presence. Candidate path selection must not be tied rigidly to RHEL major version.

### 3.5 Package Updates

Build the installed package inventory from `installed-rpms`/DNF output. Optional collected updateinfo can be used when valid, but latest/security assessment may require an advisory/reference provider. Absence of updateinfo is not itself a failure.

### 3.6 SELINUX

Read runtime and configured SELinux state from `sestatus`, `getenforce`, and `/etc/selinux/config`. Report both runtime and persistent state so mismatches are visible.

### 3.7 Firewalld

Read installed/enabled/active state plus zones/services/ports where collected. Desired state is conditional on customer host-firewall policy; enabled is not always good and disabled is not always good without context.

### 3.8 Time Synchronization

Parse Chrony configuration and runtime health separately: configured source count, reachable/usable source count, selected source, reach, stratum, offset, synchronized state and timezone. Configured-source count alone is insufficient for grading.

### 3.9 Kdump

Use systemd state, `/proc/cmdline`, `kexec_crash_size`, `kdump.conf`, panic sysctls, and optional kdumpctl/crash directory evidence. `kdumpctl_status` is optional. Normalize service state, crashkernel, reserved memory, target and panic settings.

### 3.10 System Error Logs

Search `/var/log/messages*`, dmesg and collected journal output using the configured storage/hardware and generic severity patterns. Store source/timestamp/category/severity/component/matched pattern/message/count. Generic `error`, `warn`, or `fail` matches require contextual filtering and are not automatically C.

### 3.11 Base Kernel Parameters

Read effective sysctl values from `sysctl -a` with `/proc/sys` fallback. Normalize the parameters defined by the scope, including dirty ratios, swappiness, ip_forward, somaxconn and tcp_max_syn_backlog. Context-dependent parameters such as ip_forward must retain workload applicability.

### 3.12 Default Service Enabled

Read systemd unit-files/units and wants symlinks. For each policy service, determine installed/enabled/active/masked state and evaluate applicability first—for example iSCSI, virtualization or storage-related services are judged according to actual feature use.

### 3.13 Application Core Dump

Read limits, coredump configuration, `/etc/systemd/system.conf`, `/proc/sys/kernel/core_pattern`, `/usr/lib/tmpfiles.d/systemd.conf` and `/etc/tmpfiles.d/*`. Normalize soft/hard core limits, `DefaultLimitCORE`, storage path and tmpfiles retention/exclusion. Explicitly inspect `DefaultLimitCORE=infinity` and `/var/lib/systemd/coredump` retention.

### 3.14 Logrotate / sysstat(SAR)

Parse logrotate frequency and rotate count. For sysstat, determine package presence first, then inspect `/usr/lib/systemd/system/sysstat-collect.timer`, effective override files, list-timers and optional legacy cron configuration. Normalize effective `OnCalendar`, enabled state and interval; an override takes precedence over the vendor unit.

### 3.15 Tuned

Read active/recommended/verify profile and systemd service state. Evaluate profile recommendation conditionally using VM/BM, workload role and connected-network context; do not grade profile name without context.

### 3.16 IRQ Balance Processing

Read `/etc/sysconfig/irqbalance` and systemd state. Normalize enabled/active state and `IRQBALANCE_ONESHOT`, then compare with the configured policy.

### 3.17 Timer

First inventory `systemctl list-timers --all`. Only timer units with an explicit diagnostic policy are evaluated. `dnf-makecache.timer` is currently a known policy item; unrelated timers are inventory/context only and do not become findings merely because they exist.

### 3.18 Other Settings — rsyslog / cron only

This Full diagnostic contains two subchecks only.

- rsyslog: inspect `/etc/rsyslog.d/0-ignore-systemd-session-slice.conf`; validate required filter content. If absent/mismatched, report remediation to create/update it and run `systemctl restart rsyslog` after administrator review/application.
- cron: inspect `/etc/crontab`; expected `MAILTO=""`. If `MAILTO="root"`, report remediation to change it to an empty value.

The analyzer remains read-only and never changes/restarts the customer host.

### 4.1 Bonding

Detect real bonding use from process-scoped `/proc/*/net/bonding/*`, fixed proc paths, NetworkManager profiles/nmcli where available and IP link fallback. Normalize bond count, mode, miimon/LACP, slave count/state and active slave. If bonding is not in use, mark `SKIPPED`.

### 4.2 Network Kernel Parameters

Applicability requires at least one physical NIC that is actually connected and operating at 10Gbps or faster: physical NIC=true, speed >=10000 Mbps, link detected, carrier up. Installed/capable but disconnected NICs do not qualify. For bonds, evaluate physical slave links. Only then parse sysctl, softnet_stat and NIC counters and apply the high-speed network tuning policy.

### 4.3 Netstate

Use nmcli when collected, but never require it. Fall back to `ip -s -d link`, address outputs, ethtool and NetworkManager config/journal. Normalize carrier, speed, device state, error/drop counters and NM state if available.

### 5.1 Device Mapper Multipath

Determine actual multipath use before grading. Plugin output presence alone is insufficient. Normalize driver loaded state, map count, WWID, alias, vendor/model, path count, active/failed paths, path policy and features. Vendor-specific recommended settings remain an external/internal policy dependency.

## Engine contract

1. Applicability is evaluated before A/B/C grading.
2. Missing/unusable evidence becomes internal `SKIPPED`, not customer-visible UNKNOWN.
3. Parser returns facts only; diagnostic rules consume normalized facts.
4. Source command failures are retained as evidence notes but do not create positive facts.
5. Remediation is report guidance only; the analyzer is read-only.
6. HTML, DOCX and JSON use the same diagnostic result model.
