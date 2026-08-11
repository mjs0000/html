# Diagnostic Mapping Matrix

## Basis

This matrix compares three project inputs:

- Current scope: `락플레이스_구조진단 Scope RHEL 9_v0.5.docx`.
- Legacy item list: `구조진단항목.xlsx`.
- Sample evidence: `sosreport-fujitsu-seoki-2026-04-21-eagytmz.tar(1).xz`.

The current scope contains 26 report items: System 19, Network 4, Storage 3. The legacy XLSX contains 20 items. The six items added by the current scope are Boot Parameters, Timer, 10G Environment, Netstate, I/O Scheduler, and NFS Options.

The sample sosreport is RHEL 8.10. It is used to validate sosreport path availability and parser feasibility, not to define RHEL 9 grading policy.

Customer-facing grades remain A/B/C only. Missing or insufficient evidence is handled internally as `SKIPPED` and is not rendered as UNKNOWN.

## Matrix

| Sec | ID | Item | Legacy XLSX | Automation | Parser | Primary sosreport sources | Key normalized fields | Applicability | Sample coverage |
|---|---|---|---|---|---|---|---|---|---|
| 3.1 | `SYS_HW_CERT` | 하드웨어 인증 | Y | conditional | `hardware` | `sos_commands/hardware/dmidecode`; `sos_commands/processor/lscpu`; `sos_commands/pci/lspci_-nnvv` | vendor, model, CPU, PCI/NIC | All | 3/3 |
| 3.2 | `SYS_LIFECYCLE` | Life-Cycle | Y | conditional | `lifecycle` | `etc/redhat-release`; `etc/os-release` | major/minor version | RHEL 9 | 2/2 |
| 3.3 | `SYS_BOOT_MODE` | Boot Mode | Y | full | `boot_mode` | `sos_commands/boot/ls_-alZR_.sys.firmware`; `sos_commands/boot/efibootmgr_-v` | UEFI/BIOS, BootCurrent | All | 2/2 |
| 3.4 | `SYS_FILESYSTEM` | Filesystem | Y | full | `filesystem` | `sos_commands/filesys/findmnt`; `sos_commands/filesys/df_-aliT_-x_autofs`; `sos_commands/block/lsblk_-f_-a_-l`; `etc/fstab` | mount, fstype, usage, inode, LVM, swap | All | 4/4 |
| 3.5 | `SYS_PACKAGE_UPDATE` | 주요 패키지 업데이트 | Y | conditional | `packages` | `installed-rpms`; `sos_commands/dnf/dnf_list_installed`; `sos_commands/dnf/dnf_updateinfo_list_--available` | package/advisory/kernel | RPM/DNF | 3/3 |
| 3.6 | `SYS_SELINUX` | SELINUX | Y | full | `selinux` | `sos_commands/selinux/sestatus` | status/mode | All | 1/1 |
| 3.7 | `SYS_FIREWALLD` | Firewalld | Y | conditional | `firewalld` | `sos_commands/systemd/systemctl_list-unit-files`; `sos_commands/firewalld/firewall-cmd_--list-all-zones` | active/enabled/zones/services/ports | firewalld | 2/2 |
| 3.8 | `SYS_TIME_SYNC` | 시간 동기화 | Y | full | `chrony` | `sos_commands/chrony/chronyc_-n_sources`; `sos_commands/chrony/chronyc_tracking`; `etc/chrony.conf`; `sos_commands/systemd/timedatectl` | source count, selected source, offset, slew, timezone | chrony | 4/4 |
| 3.9 | `SYS_KDUMP` | 덤프 수집(Kdump) | Y | full | `kdump` | `sos_commands/kdump/kdumpctl_status`; `proc/cmdline`; `sys/kernel/kexec_crash_size`; `sos_commands/kernel/sysctl_-a` | operational, crashkernel, reserved memory, panic sysctl | All | 4/4 |
| 3.10 | `SYS_ERROR_LOG` | 시스템 에러 로그 | Y | full | `error_log` | `var/log/messages`; rotated `messages-*` | keyword/event/severity | rsyslog | 1/1 |
| 3.11 | `SYS_KERNEL_PARAM` | 기본 커널 파라미터 | Y | full | `sysctl` | `sos_commands/kernel/sysctl_-a` | dirty ratios, swappiness, ip_forward, somaxconn, syn backlog | All | 1/1 |
| 3.12 | `SYS_BOOT_PARAM` | 부팅 파라미터 | NEW | full | `boot_parameters` | `proc/cmdline` | token set, crashkernel, THP/IOMMU/audit | All | 1/1 |
| 3.13 | `SYS_DEFAULT_SERVICE` | Default Service Enabled | Y | conditional | `services` | `sos_commands/systemd/systemctl_list-unit-files`; `sos_commands/systemd/systemctl_list-units` | service enabled/active | systemd | 2/2 |
| 3.14 | `SYS_APP_COREDUMP` | Application Core Dump | Y | full | `coredump` | `etc/security/limits.conf`; `etc/systemd/coredump.conf`; `usr/lib/sysctl.d/50-coredump.conf` | core limits/pattern/storage/retention | All | 3/3 |
| 3.15 | `SYS_LOGROTATE_SYSSTAT` | Logrotate / sysstat(SAR) | Y | full | `logrotate_sysstat` | `etc/logrotate.conf`; `sos_commands/logrotate/logrotate_debug`; `usr/lib/systemd/system/sysstat-collect.timer` | rotate cadence/count, SAR interval | All | 3/3 |
| 3.16 | `SYS_TUNED` | Tuned | Y | conditional | `tuned` | `sos_commands/tuned/tuned-adm_active`; `sos_commands/tuned/tuned-adm_recommend`; systemd unit files | active/recommended profile, system type, NIC speed | tuned target | 3/3 |
| 3.17 | `SYS_IRQBALANCE` | IRQ Balance Processing | Y | full | `irqbalance` | `etc/sysconfig/irqbalance`; systemd unit files | enabled/active/ONESHOT | All | 2/2 |
| 3.18 | `SYS_TIMER` | Timer | NEW | full | `systemd_timer` | `sos_commands/systemd/systemctl_list-timers_--all`; unit files | timer states, dnf-makecache, sysstat timer | systemd | 2/2 |
| 3.19 | `SYS_OTHER_SETTINGS` | 기타 설정 | Y | conditional | `other_settings` | `etc/profile`; `etc/crontab`; `etc/rsyslog.d/*` | history logging, session filter, MAILTO | Environment | 1/2 primary |
| 4.1 | `NET_BONDING` | 이중화 (Bonding) | Y | conditional | `bonding` | `proc/net/bonding/*`; `sos_commands/networkmanager/nmcli_con` | mode, miimon, slaves, active slave, LACP | Bond users | 1/2 primary |
| 4.2 | `NET_10G` | 10G 환경 설정 | NEW | conditional | `network_10g` | `sos_commands/networking/ethtool_*`; `sos_commands/networking/ethtool_-g_*` | speed, ring current/max, drop/FIFO/CRC | >=10G physical NIC | 2/2 |
| 4.3 | `NET_KERNEL_PARAM` | 네트워크 커널 파라미터 | Y | conditional | `network_sysctl` | `sos_commands/kernel/sysctl_-a`; `proc/net/softnet_stat`; ethtool stats | backlog, budget, tcp buffers, socket max, min_free_kbytes, drops | High-speed network | 1/1 primary |
| 4.4 | `NET_NETSTATE` | Netstate | NEW | full | `netstate` | `sos_commands/networkmanager/nmcli_general_status`; `sos_commands/networkmanager/nmcli_dev`; ethtool | NM state, link, speed, error/drop counters | NIC | 2/2 |
| 5.1 | `STG_IO_SCHEDULER` | I/O Scheduler | NEW | conditional | `io_scheduler` | `sos_commands/block/lsblk_-t`; sysfs `queue/scheduler` | device type/transport/rotational/scheduler | Block devices | 1/1 |
| 5.2 | `STG_MULTIPATH` | Device Mapper Multipath | Y | conditional | `multipath` | `sos_commands/multipath/multipath_-ll`; `sos_commands/multipath/multipathd_show_config`; `etc/multipath.conf` | map, WWID, vendor/model, path state/policy | Multipath users | 2/2 primary |
| 5.3 | `STG_NFS_OPTIONS` | NFS Options | NEW | conditional | `nfs` | `sos_commands/nfs/mountstats_-n`; `proc/mounts`; nfsstat | server, mountpoint, version/options, rsize/wsize/timeo/retrans | NFS clients | 2/2 primary |

## Important rule decisions

### External or context-dependent items

The following cannot be safely graded from sosreport facts alone:

- Hardware certification: sosreport identifies vendor/model, but certification requires Red Hat Catalog or an internal certification reference.
- Life-Cycle: OS version is available locally; support dates and final minor release are policy/reference data.
- Firewalld: the desired state depends on whether host firewall policy is required and whether an external firewall exists.
- Default services: services such as iSCSI, libvirt, qemu-guest-agent, KSM, and storage-related services require workload applicability checks.
- Tuned: VM/BM, DB workload, and 10G network context affect the recommended profile.
- Network tuning and I/O Scheduler: recommendations are device/workload dependent.
- Multipath: path health is local, but vendor-specific configuration recommendations require external/internal policy.

These items must use explicit applicability/context rules. An unused feature must not become grade C simply because its configuration does not match a recommendation intended for users of that feature.

## Sample validation observations

The attached sample proves that the planned parsers can find real evidence for the majority of items. Examples include:

- Boot: `efibootmgr_-v` and `/sys/firmware` data are present.
- Filesystem: findmnt, df, lsblk, fstab, LVM and swap data are present.
- SELinux: `sestatus` is present.
- Time sync: chronyc sources/tracking and `chrony.conf` are present.
- Kdump: `kdumpctl_status`, crashkernel command line, reserved-memory sysfs and sysctl data are present.
- Tuned: active/recommended profile data is present.
- Storage: `multipath -ll` and multipathd configuration are present.
- Network: extensive NetworkManager and ethtool data are present.
- NFS: mountstats/nfsstat/proc mounts data are present.

The sample is RHEL 8.10, so source paths are validated against RHEL 8 sosreport behavior. The implementation must support candidate-path fallback rather than hard-code a single sosreport version.

## Engine contract

1. Archive reader safely extracts the archive and resolves the sosreport root.
2. Mapping definitions locate candidate evidence files.
3. Parsers return normalized facts only; they do not assign grades.
4. Applicability is evaluated before grading.
5. Rule engine assigns A/B/C using version-aware policy.
6. Missing required evidence becomes internal `SKIPPED`; it is not shown as UNKNOWN in customer reports.
7. Multiple host results are aggregated into one `DiagnosticReport` and rendered by both HTML and DOCX renderers.
8. Evidence paths and excerpts are retained internally for traceability even if the customer report hides detailed evidence by default.
