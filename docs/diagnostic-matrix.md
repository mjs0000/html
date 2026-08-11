# Diagnostic Mapping Matrix v2

## Comparison basis

This revision compares all currently available project materials:

- `락플레이스_구조진단 Scope RHEL 9_v0.5.docx` — authoritative current diagnostic scope and recommendations.
- `구조진단항목.xlsx` — legacy 20-item diagnostic list.
- `sosreport-fujitsu-seoki-2026-04-21-eagytmz.tar(1).xz` — RHEL 8.10 fixture.
- `sosreport-haserpapp1-2024-11-05-xjajess.tar.xz` — RHEL 9.2 fixture.
- `sosreport-haserpapq1-2024-11-06-dvndpsm.tar.xz` — RHEL 9.2 fixture.
- `sosreport-haserpdbp1-2024-11-03-htzyqoo.tar.xz` — RHEL 9.2 fixture.
- `sosreport-haspoapp1-2024-11-06-qtyciec.tar.xz` — RHEL 9.2 fixture.
- `sosreport-haspodbp1-2024-11-06-fcupecg.tar.xz` — RHEL 9.2 fixture.

Current scope = 26 items: System 19, Network 4, Storage 3. Legacy XLSX = 20 items. New current-scope items are Boot Parameters, Timer, 10G Environment, Netstate, I/O Scheduler, and NFS Options.

Customer-facing grades remain A/B/C only. Missing evidence is internal `SKIPPED`; `UNKNOWN` is not rendered.

## Fixture summary

| Host | RHEL | Observed fixture characteristics useful for tests |
|---|---|---|
| fujitsu-seoki | 8.10 | UEFI, SELinux disabled, 4 chrony sources, 10G evidence, multipath present, NFS present, tuned `network-latency` |
| haserpapp1 | 9.2 | UEFI, SELinux disabled, 1 chrony source, 3 bonds, 10G, multipath present, NFS present, tuned `sap-netweaver` |
| haserpapq1 | 9.2 | UEFI, SELinux disabled, 1 chrony source, 3 bonds, 10G, multipath present, NFS present, tuned `sap-netweaver` |
| haserpdbp1 | 9.2 | UEFI, SELinux disabled, 1 chrony source, 4 bonds, 10G, no multipath maps, no NFS mounts, TuneD daemon not running / preset `sap-hana` |
| haspoapp1 | 9.2 | UEFI, SELinux disabled, 1 chrony source, 3 bonds, 10G, multipath present, NFS present, tuned `sap-netweaver` |
| haspodbp1 | 9.2 | UEFI, SELinux disabled, 1 chrony source, 4 bonds, 10G, no multipath maps, no NFS mounts, tuned `sap-hana` |

These fixtures give useful positive/negative applicability cases for Bonding, 10G, Multipath, NFS and Tuned. They should become parser/integration-test fixtures after sanitization or reduced fixture extraction.

## Full mapping matrix

| Sec | ID | Item | XLSX | Auto | Parser | Preferred sources and fallbacks | Normalized fields | Applicability / policy dependency | Validation across 6 fixtures |
|---|---|---|---|---|---|---|---|---|---|
| 3.1 | `SYS_HW_CERT` | 하드웨어 인증 | Y | conditional | `hardware` | `sos_commands/hardware/dmidecode`, `sos_commands/processor/lscpu`, `sos_commands/pci/lspci_-nnvv` | system vendor/model, CPU, NIC/PCI IDs | Hardware certification requires Red Hat Catalog/internal reference | Sources present 6/6 |
| 3.2 | `SYS_LIFECYCLE` | Life-Cycle | Y | conditional | `lifecycle` | `etc/redhat-release`, `etc/os-release`, kernel uname | major/minor, kernel release | Support dates/latest minor/EUS/ELS require versioned reference data | Sources present 6/6; fixtures cover 8.10 and 9.2 |
| 3.3 | `SYS_BOOT_MODE` | Boot Mode | Y | full | `boot_mode` | Primary `sos_commands/boot/efibootmgr_-v`; firmware listing fallback: RHEL8 `ls_-alZR_.sys.firmware`, RHEL9 `ls_-lanR_.sys.firmware`; `mokutil_--sb-state` for Secure Boot | boot mode, BootCurrent, EFI entries, secure_boot | All systems; Boot Mode and Secure Boot are separate facts | `efibootmgr` present 6/6; firmware command name differs by sos/RHEL generation |
| 3.4 | `SYS_FILESYSTEM` | Filesystem | Y | full | `filesystem` | `findmnt`, `lsblk_-f_-a_-l`, `etc/fstab`; df fallback RHEL8 `df_-aliT_-x_autofs`, RHEL9 `df_-ali_-x_autofs`; LVM and swap sources | mount, source, fstype, size/use%, inode use%, LVM, swap | All; NFS filesystems handled additionally by NFS rule | Core evidence 6/6; df filename variant confirmed |
| 3.5 | `SYS_PACKAGE_UPDATE` | 주요 패키지 업데이트 | Y | conditional | `packages` | `installed-rpms`, `dnf_list_installed`; optional `dnf_updateinfo*`; yum/dnf history | installed NEVRA, kernel, advisory evidence | “Latest/security update” requires external repo/advisory reference when updateinfo not collected | installed package evidence 6/6; updateinfo absent in all 5 RHEL9 fixtures |
| 3.6 | `SYS_SELINUX` | SELINUX | Y | full | `selinux` | `sos_commands/selinux/sestatus`, fallback `etc/selinux/config` | enabled, current mode, config mode | All | `sestatus` present 6/6 |
| 3.7 | `SYS_FIREWALLD` | Firewalld | Y | conditional | `firewalld` | systemd unit-files/units, `firewall-cmd_--list-all-zones`, firewalld config | installed, active, enabled, zones, services, ports, rich rules | Desired enabled/disabled state depends on customer host-firewall policy | Evidence present 6/6 |
| 3.8 | `SYS_TIME_SYNC` | 시간 동기화 | Y | full | `chrony` | `chronyc_-n_sources`, `chronyc_tracking`, `chronyc_sourcestats`, `etc/chrony.conf`, `timedatectl` | source count, selected source, reach, offset, stratum, slew/leap config, timezone, sync state | Chrony/NTP clients; source-count threshold comes from scope policy | Evidence present 6/6; fixtures provide 1-source and 4-source cases |
| 3.9 | `SYS_KDUMP` | 덤프 수집 | Y | full | `kdump` | `proc/cmdline`, `sys/kernel/kexec_crash_size`, `etc/kdump.conf`, systemd unit status/enabled; optional `kdumpctl_status`; `sysctl_-a`; crash directory metadata | crashkernel, reserved memory, enabled/active, dump target, panic sysctls | All; some panic values are operational-policy dependent | Core evidence 6/6. `kdumpctl_status` exists in the RHEL8 fixture but is absent in 5 RHEL9 fixtures, so it cannot be mandatory |
| 3.10 | `SYS_ERROR_LOG` | 시스템 에러 로그 | Y | full | `error_log` | `var/log/messages`, rotated messages; journal text where collected | timestamp, keyword class, component, message, count | All; keyword list/versioning must be policy data | messages evidence 6/6 |
| 3.11 | `SYS_KERNEL_PARAM` | 기본 커널 파라미터 | Y | full | `sysctl` | `sos_commands/kernel/sysctl_-a`; `/proc/sys/*` fallback | dirty ratios, swappiness, ip_forward, somaxconn, tcp_max_syn_backlog and configured overrides | `ip_forward` is workload dependent; other thresholds are scope policy | sysctl present 6/6 |
| 3.12 | `SYS_BOOT_PARAM` | 부팅 파라미터 | NEW | full | `boot_parameters` | `proc/cmdline`, grub config/defaults where collected | normalized kernel command-line tokens and values | Rule set must explicitly name required/prohibited/conditional tokens | `proc/cmdline` present 6/6 |
| 3.13 | `SYS_DEFAULT_SERVICE` | Default Service Enabled | Y | conditional | `services` | `systemctl_list-unit-files`, `systemctl_list-units`, unit symlinks | service installed/enabled/active/masked | Most listed services require feature/workload applicability; unconditional-disable list can be separate | systemd evidence present 6/6 |
| 3.14 | `SYS_APP_COREDUMP` | Application Core Dump | Y | full | `coredump` | `etc/security/limits.conf` + limits.d, `etc/systemd/coredump.conf` + coredump.conf.d, `usr/lib/sysctl.d/50-coredump.conf`, `/proc/sys/kernel/core_pattern`, tmpfiles config | hard/soft core limit, core pattern, storage, compression, retention | All; report should distinguish capture capability and retention | Main evidence present 6/6 |
| 3.15 | `SYS_LOGROTATE_SYSSTAT` | Logrotate / sysstat(SAR) | Y | full + applicability | `logrotate_sysstat` | `etc/logrotate.conf`, `etc/logrotate.d/*`, `sos_commands/logrotate/logrotate_debug`; sysstat: package evidence, `sysstat-collect.timer` when installed, timer list, cron fallback | logrotate frequency/rotate count, sysstat installed/enabled, collection interval | If sysstat package/timer absent, absence is an observable condition; timer file must not be treated as generic missing evidence | logrotate evidence 6/6; sysstat timer present in RHEL8 fixture but absent in all 5 RHEL9 fixtures |
| 3.16 | `SYS_TUNED` | Tuned | Y | conditional | `tuned` | `tuned-adm_active`, `tuned-adm_recommend`, service status, `/etc/tuned/active_profile`; system type + NIC speed | daemon state, active/recommended/preset profile, VM/BM, workload hints, NIC speed | Recommended profile depends on VM/BM, SAP/DB/app workload and 10G; web metadata may need workload input | Evidence 6/6; fixtures cover sap-netweaver, sap-hana, network-latency and daemon-not-running case |
| 3.17 | `SYS_IRQBALANCE` | IRQ Balance Processing | Y | full | `irqbalance` | `etc/sysconfig/irqbalance`, systemd unit-files/units | installed, enabled, active, IRQBALANCE_ONESHOT | All except explicitly workload/vendor-excluded cases | Evidence 6/6 |
| 3.18 | `SYS_TIMER` | Timer | NEW | full | `systemd_timer` | `systemctl_list-timers_--all`, unit files and enablement symlinks | timer name, enabled, active, next/last run; dnf-makecache state | systemd systems | timer list present 6/6 |
| 3.19 | `SYS_OTHER_SETTINGS` | 기타 설정 | Y | conditional | `other_settings` | `etc/profile`, profile.d, rsyslog.d; cron sources: `/etc/cron*` and `sos_commands/cron/*` rather than assuming `/etc/crontab` always collected | history logging, rsyslog session-slice filter, cron MAILTO/output handling | Customer/access-control policy dependent | profile present 6/6; `/etc/crontab` is not reliable across the fixtures, so cron plugin/config fallbacks are required |
| 4.1 | `NET_BONDING` | 이중화 (Bonding) | Y | conditional | `bonding` | dynamic `proc/<pid>/net/bonding/*`, `/proc/net/bonding/*` if present, NetworkManager connection profiles, `nmcli_con_show_id_bond*`, `ip_-d_link` | bond name/mode/miimon/LACP/slaves/active slave/link state | Only bonding users; mode recommendation depends on network design | Dynamic proc path confirmed in all 5 RHEL9 fixtures; RHEL8 fixture is a no-bond applicability case |
| 4.2 | `NET_10G` | 10G 환경 설정 | NEW | conditional | `network_10g` | `ethtool_<if>`, `ethtool_-g_<if>`, `ethtool_-S_<if>`, `ip_-s_link` | speed, ring current/max, rx/tx drop, FIFO/CRC/errors | Only physical NICs >=10G; tuning depends on error/drop evidence and vendor constraints | ethtool/ring evidence 6/6; all fixtures include 10G evidence |
| 4.3 | `NET_KERNEL_PARAM` | 네트워크 커널 파라미터 | Y | conditional | `network_sysctl` | `sysctl_-a`; dynamic `proc/<pid>/net/softnet_stat`; ethtool/ip counters | netdev_max_backlog, netdev_budget, tcp_rmem/wmem, rmem/wmem max, min_free_kbytes, drop/budget counters | High-speed/problem context; do not grade thresholds without applicability | sysctl + softnet evidence 6/6; dynamic proc path is required |
| 4.4 | `NET_NETSTATE` | Netstate | NEW | full | `netstate` | `nmcli_general_status`, `nmcli_dev`, `ip_-s_link`, ethtool | NetworkManager state, device state, carrier, speed, errors/drops | NIC/NetworkManager systems | Evidence 6/6 |
| 5.1 | `STG_IO_SCHEDULER` | I/O Scheduler | NEW | conditional | `io_scheduler` | `lsblk_-t`, dynamic sysfs `.../block/<dev>/queue/scheduler`, device/transport facts | device, rota, transport, scheduler, selected scheduler | Scheduler recommendation depends on RHEL version/device type/storage stack | lsblk + scheduler sysfs evidence 6/6 |
| 5.2 | `STG_MULTIPATH` | Device Mapper Multipath | Y | conditional | `multipath` | `multipath_-ll`, `multipathd_show_config`, `etc/multipath.conf`, device-mapper/fibrechannel facts | map/alias/WWID/vendor/model/path count/path state/policy/features | Only multipath clients; vendor-specific settings need policy/reference | Sources 6/6; fixtures include both active multipath maps and zero-map cases |
| 5.3 | `STG_NFS_OPTIONS` | NFS Options | NEW | conditional | `nfs` | RHEL8 may collect `sos_commands/nfs/mountstats_-n`; RHEL9 fixtures require dynamic `proc/<pid>/mountstats` / proc mounts + `nfsstat_-o_all`; `etc/fstab` | server/export/mountpoint/version/options/rsize/wsize/timeo/retrans | Only NFS clients | NFS plugin evidence 6/6; mountstats command-path differs. Fixtures include NFS-present and NFS-absent cases |

## Sosreport-version path differences confirmed

The comparison exposed several cases that must be represented as candidate paths/patterns, not single hard-coded paths:

1. Boot firmware listing: RHEL8 fixture uses `ls_-alZR_.sys.firmware`; RHEL9.2 fixtures use `ls_-lanR_.sys.firmware`.
2. Filesystem `df`: RHEL8 fixture provides `df_-aliT_-x_autofs`; RHEL9.2 fixtures provide `df_-ali_-x_autofs`.
3. Kdump: `kdumpctl_status` is available in the RHEL8 fixture but absent in all five RHEL9.2 fixtures. Use systemd, `kexec_crash_size`, `proc/cmdline`, `etc/kdump.conf` and sysctl as the core evidence set.
4. Bonding: RHEL9 fixtures store bond state under dynamic process-scoped paths such as `proc/<pid>/net/bonding/bond0`; fixed `proc/net/bonding/*` alone is insufficient.
5. Network softnet: likewise `proc/<pid>/net/softnet_stat` is the reliable collected path pattern.
6. NFS mountstats: explicit `sos_commands/nfs/mountstats_-n` exists in the RHEL8 fixture, while the RHEL9 fixtures rely on process-scoped mountstats plus `nfsstat`/mount data.
7. Package updates: installed package inventory is consistently present, but online/available updateinfo is not guaranteed in the RHEL9 fixtures; “latest update” grading needs reference data outside the archive.
8. Sysstat: timer evidence is conditional on package/configuration presence and must be preceded by package/applicability detection.

## Resulting parser design rules

- Mapping sources use ordered candidate lists and glob/regex patterns.
- Dynamic `/proc/<pid>/...` data must be resolved by pattern and preferably normalized to a canonical evidence label such as `proc/*/net/bonding/*`.
- A parser returns facts only. It never assigns A/B/C.
- Applicability runs before grading: no Multipath/NFS/Bonding/sysstat use is not the same as missing evidence.
- Context/external-reference items explicitly declare required context inputs or reference datasets.
- Missing required evidence after candidate resolution produces internal `SKIPPED`, not a customer-visible UNKNOWN.
- The same normalized result model feeds HTML and DOCX.

## Recommended implementation/test split

The six archives should be used as a regression corpus, but production tests should use reduced/sanitized fixtures containing only the files required for each parser. Recommended fixture groups:

- Boot/Filesystem/SELinux/Chrony: one RHEL8 and one RHEL9 fixture.
- Kdump: RHEL8 case with `kdumpctl_status`; RHEL9 case without it.
- Tuned: sap-netweaver, sap-hana, daemon-not-running, and generic network-latency cases.
- Bonding/10G: RHEL9 hosts with 3-bond and 4-bond configurations plus RHEL8 no-bond case.
- Multipath: active-map and zero-map cases.
- NFS: multiple mounts, one mount, and no-mount cases.
