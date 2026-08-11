# Diagnostic Mapping Matrix v3

## Comparison basis

This revision compares the current RockPLACE RHEL scope, the legacy XLSX list, and **11 real sosreport archives**.

### Documents

- `락플레이스_구조진단 Scope RHEL 9_v0.5.docx` — authoritative current diagnostic scope/policy source.
- `구조진단항목.xlsx` — legacy 20-item list.
- Previous RockPLACE Health Check PDF — presentation/reference format only, not diagnostic policy.

### Sosreport corpus

- `fujitsu-seoki` — RHEL 8.10.
- `haserpapp1`, `haserpapq1`, `haserpdbp1`, `haspoapp1`, `haspodbp1` — RHEL 9.2.
- `BD-L2-SMCPAPP01NEW`, `BD-L2-SMCPFIDO01NEW`, `BD-L2-SMCPOIDCWAS01NEW`, `BD-L2-SMCPOIDCWEB01NEW`, `BD-L2-SMCPONM01NEW` — RHEL 8.10.

Current scope remains **26 report items: System 19 + Network 4 + Storage 3**. The current-scope-only additions relative to the legacy XLSX are Boot Parameters, Timer, 10G Environment, Netstate, I/O Scheduler and NFS Options.

Customer-facing grades are A/B/C only. Missing required evidence after candidate resolution is internal `SKIPPED`; customer reports do not render UNKNOWN.

## New evidence learned from the additional five RHEL 8.10 archives

The five newly supplied BD-L2 fixtures add several important cases that were not covered clearly enough by the earlier corpus:

- All five are **Dell PowerEdge R760** systems.
- `efibootmgr_-v` files exist, but the command output is `efibootmgr: No such file or directory`; therefore **file existence must never be treated as positive EFI evidence**.
- Their `/sys/firmware` listings do not contain `/sys/firmware/efi`, and `/boot/efi` is not mounted in the collected `findmnt`/fstab evidence. These are strong Legacy/BIOS examples when the firmware listing is complete.
- All five use RHEL 8.10-style `ls_-lanR_.sys.firmware` and `df_-ali_-x_autofs` source names, confirming that command-output filenames vary by sos version, not just OS major version.
- All five have two configured Chrony sources. Four show reachable/selected sources; one fixture (`SMCPOIDCWEB01NEW`) shows both sources unreachable (`^?`, Reach 0). This provides a valuable “configured sources != synchronized sources” test case.
- All five have Bonding evidence under dynamic `proc/<pid>/net/bonding/*`; four have two bonds and one has one bond.
- All five expose 10Gbps interfaces through plain `sos_commands/networking/ethtool_<iface>` output.
- All five have `multipath_-ll`, but it explicitly reports no `/etc/multipath.conf`, blacklisting all devices, and `DM multipath kernel driver not loaded`; this is an excellent “plugin evidence exists but feature is not applicable” case.
- All five have NFS plugin/proc evidence files but no NFS mounts; again, source-file existence is not applicability.
- All five lack the sysstat package/timer, while `systemctl_list-timers_--all` is present. Sysstat applicability must therefore be checked from package/service evidence before timer grading.
- Kdump is enabled and active in systemd in all five even though `kdumpctl_status` is absent, further confirming that `kdumpctl_status` is optional evidence.
- NetworkManager `nmcli_*` command outputs are absent in these five archives. Netstate must therefore fall back to `ip_-s_-d_link`, `ip_-d_address`, `ip_-o_addr`, ethtool, NetworkManager config/journal evidence.

## Fixture capability summary

| Fixture group | RHEL | Boot cases | Chrony cases | Bonding | 10G | Multipath | NFS | Tuned / special value |
|---|---:|---|---|---|---|---|---|---|
| fujitsu-seoki | 8.10 | UEFI positive | 4 sources | no/limited bond case | yes | active maps | present | `network-latency` |
| haserp/haspo 5 hosts | 9.2 | UEFI positive | 1 source | 3/4 bonds | yes | active + zero-map cases | present + absent cases | `sap-netweaver`, `sap-hana`, daemon-not-running |
| BD-L2 5 hosts | 8.10 | Legacy/BIOS evidence; efibootmgr command failure | 2 sources; includes unreachable case | 1/2 bonds | yes | driver not loaded / no maps | no mounts | `throughput-performance` |

This corpus is now suitable for path-compatibility and applicability regression tests across RHEL 8/9 and different sosreport collection behavior.

## Full diagnostic Mapping Matrix

| Sec | ID | Item | XLSX | Automation | Parser | Preferred sosreport evidence / fallbacks | Normalized facts | Applicability / external dependency | Corpus validation |
|---|---|---|---|---|---|---|---|---|---|
| 3.1 | `SYS_HW_CERT` | 하드웨어 인증 | Y | conditional | `hardware` | `dmidecode`, `lscpu`, `lspci_-nnvv` | vendor/model, CPU, PCI/NIC IDs | Certification itself requires Red Hat Catalog/internal reference | 11 fixtures provide hardware facts; includes Dell R760 plus other models |
| 3.2 | `SYS_LIFECYCLE` | Life-Cycle | Y | conditional | `lifecycle` | `etc/redhat-release`, `etc/os-release`, uname | RHEL major/minor, kernel | Support dates/latest minor/EUS/ELS require versioned reference | Corpus covers RHEL 8.10 and 9.2 |
| 3.3 | `SYS_BOOT_MODE` | Boot Mode | Y | full | `boot_mode` | `/sys/firmware` listing variants; validated `efibootmgr_-v`; `/boot/efi` as supporting evidence; `mokutil` separately for Secure Boot | `boot_mode`, evidence confidence, BootCurrent, EFI entries, secure_boot | All. EFI command file existence is insufficient; command must have valid output | UEFI-positive and Legacy/BIOS-positive cases now both available |
| 3.4 | `SYS_FILESYSTEM` | Filesystem | Y | full | `filesystem` | `findmnt`, `lsblk_-f_-a_-l`, `df_*autofs`, `fstab`, LVM, swap | mount/source/fstype/usage/inode/LVM/swap | All; remote FS also feeds NFS rule | Multiple `df` filename variants confirmed across corpus |
| 3.5 | `SYS_PACKAGE_UPDATE` | 주요 패키지 업데이트 | Y | conditional | `packages` | `installed-rpms`, `dnf_list_installed`, optional `dnf_updateinfo*`, dnf/yum history | NEVRA, kernel, available advisory evidence | Latest/security assessment needs external repo/advisory data when updateinfo absent | Package inventory reliable; available updateinfo not reliable |
| 3.6 | `SYS_SELINUX` | SELINUX | Y | full | `selinux` | `sestatus`, `getenforce`, `etc/selinux/config` | runtime/config mode | All | Source pattern stable; disabled examples abundant |
| 3.7 | `SYS_FIREWALLD` | Firewalld | Y | conditional | `firewalld` | systemd state, `firewall-cmd_--list-all-zones`, config | installed/active/enabled/zones/services/ports/rules | Desired state needs customer host-firewall context | Evidence patterns available throughout corpus |
| 3.8 | `SYS_TIME_SYNC` | 시간 동기화 | Y | full | `chrony` | `chronyc_-n_sources`, tracking, sourcestats, `chrony.conf`, timedatectl | configured source count, reachable count, selected source, reach, offset, stratum, leap/slew, timezone/sync state | Chrony clients | Corpus now includes 1/2/4-source and unreachable-source cases; grade must not use source count alone |
| 3.9 | `SYS_KDUMP` | 덤프 수집 | Y | full | `kdump` | systemd enabled/active, `proc/cmdline`, `kexec_crash_size`, `kdump.conf`, sysctl; optional `kdumpctl_status`, crash dir | service state, crashkernel, reserved memory, target, panic sysctls | All; selected panic settings may be policy-dependent | `kdumpctl_status` present only in some archives; systemd/core evidence works broadly |
| 3.10 | `SYS_ERROR_LOG` | 시스템 에러 로그 | Y | full | `error_log` | `var/log/messages*`, collected journal text | event timestamp/category/component/message/count | All; keyword catalog is versioned policy | Log sources available across corpus |
| 3.11 | `SYS_KERNEL_PARAM` | 기본 커널 파라미터 | Y | full | `sysctl` | `sysctl_-a`, `/proc/sys/*` fallback | dirty ratios, swappiness, ip_forward, somaxconn, syn backlog, overrides | `ip_forward` workload-dependent; thresholds from scope | sysctl stable across corpus |
| 3.12 | `SYS_BOOT_PARAM` | 부팅 파라미터 | NEW | full | `boot_parameters` | `proc/cmdline`, grub defaults/config | normalized command-line token map | Rule must explicitly label unconditional vs contextual token expectations | `proc/cmdline` broadly available |
| 3.13 | `SYS_DEFAULT_SERVICE` | Default Service Enabled | Y | conditional | `services` | systemd unit-files/units, wants symlinks | installed/enabled/active/masked | Feature/workload checks required for iSCSI, virtualization, storage, etc. | systemd evidence stable across corpus |
| 3.14 | `SYS_APP_COREDUMP` | Application Core Dump | Y | full | `coredump` | limits.conf/d, coredump.conf/d, core_pattern, tmpfiles | soft/hard core limit, pattern, storage/compression/retention | All | Multiple config fallback paths required |
| 3.15 | `SYS_LOGROTATE_SYSSTAT` | Logrotate / sysstat(SAR) | Y | full + applicability | `logrotate_sysstat` | logrotate config/debug; sysstat package first, timer/cron second | logrotate cadence/retention; sysstat installed/enabled/interval | sysstat absence is an observable result, not missing evidence | Corpus includes sysstat-present and sysstat-absent cases |
| 3.16 | `SYS_TUNED` | Tuned | Y | conditional | `tuned` | `tuned-adm_active/recommend/verify`, active_profile, systemd + system/workload/NIC facts | daemon state, active/recommended profile, VM/BM, workload, NIC speed | Recommendation depends on VM/BM, SAP/DB/app, 10G | Corpus has `network-latency`, `sap-netweaver`, `sap-hana`, `throughput-performance`, daemon-not-running |
| 3.17 | `SYS_IRQBALANCE` | IRQ Balance Processing | Y | full | `irqbalance` | `/etc/sysconfig/irqbalance`, systemd state | enabled/active/ONESHOT | All unless explicitly excluded by workload/vendor policy | Source pattern available across corpus |
| 3.18 | `SYS_TIMER` | Timer | NEW | full | `systemd_timer` | `systemctl_list-timers_--all`, unit files/symlinks | timer state, next/last run, dnf-makecache, sysstat timer | systemd systems | Timer list remains useful even when sysstat timer absent |
| 3.19 | `SYS_OTHER_SETTINGS` | 기타 설정 | Y | conditional | `other_settings` | profile/profile.d, rsyslog.d, `/etc/cron*`, `sos_commands/cron/*` | history logging, session filtering, MAILTO/output handling | Customer access/logging policy | Cron/config collection is inconsistent; broad fallback needed |
| 4.1 | `NET_BONDING` | 이중화 (Bonding) | Y | conditional | `bonding` | `proc/*/net/bonding/*`, fixed proc fallback, NM profiles, nmcli where available, `ip_-s_-d_link` | bond mode, miimon, LACP, slaves, active slave, link state | Only bonding users; topology/design determines recommended mode | Corpus includes no-bond, 1-bond, 2-bond, 3-bond and 4-bond examples |
| 4.2 | `NET_10G` | 10G 환경 설정 | NEW | conditional | `network_10g` | plain `ethtool_<iface>`, `ethtool_-g_*`, `ethtool_-S_*`, `ip_-s_-d_link` | link speed, ring current/max, RX/TX drop/FIFO/CRC/error | Only physical >=10G NICs; tuning requires counters/vendor context | New BD-L2 fixtures confirm plain ethtool speed=10000Mb/s and ring/stat sources |
| 4.3 | `NET_KERNEL_PARAM` | 네트워크 커널 파라미터 | Y | conditional | `network_sysctl` | sysctl, `proc/*/net/softnet_stat`, ethtool/IP counters | backlog/budget/TCP buffers/socket max/min_free_kbytes/drop counters | Apply thresholds only with high-speed/problem context | Dynamic softnet path confirmed repeatedly |
| 4.4 | `NET_NETSTATE` | Netstate | NEW | full | `netstate` | nmcli when collected; fallback `ip_-s_-d_link`, `ip_-d_address`, `ip_-o_addr`, ethtool, NM config/journal | NM state if available, carrier, speed, device state, error/drop counters | NIC systems | New five archives have no nmcli outputs, proving nmcli cannot be mandatory |
| 5.1 | `STG_IO_SCHEDULER` | I/O Scheduler | NEW | conditional | `io_scheduler` | `lsblk_-t`, sysfs `*/block/*/queue/scheduler`, device context | device/rota/transport/scheduler | Depends on RHEL/device/storage stack | sysfs/lsblk candidate approach retained |
| 5.2 | `STG_MULTIPATH` | Device Mapper Multipath | Y | conditional | `multipath` | `multipath_-ll`, multipathd config, multipath.conf, FC/device-mapper context | applicable, driver_loaded, maps, WWID/vendor/model/path state/policy | Only multipath clients; vendor settings need reference | Corpus includes active maps, zero maps, and explicit “driver not loaded/blacklisting all devices” cases |
| 5.3 | `STG_NFS_OPTIONS` | NFS Options | NEW | conditional | `nfs` | RHEL8 command mountstats when present; `proc/*/mountstats`, `proc/*/mounts`, nfsstat, fstab | applicable, server/export/mountpoint/version/options/rsize/wsize/timeo/retrans | Only NFS clients | Corpus includes NFS-present and plugin-present-but-no-NFS-mount cases |

## Critical implementation rules derived from all 11 archives

1. **Presence of a sos command output file is not proof of a fact.** The parser must validate command success/content. The new `efibootmgr_-v` failure cases demonstrate this directly.
2. **Applicability is separate from evidence availability.** Multipath, NFS, Bonding and sysstat plugins may be collected even when the feature is not in use.
3. **Use ordered candidate paths/patterns.** sosreport filenames vary with sos/RHEL versions and plugins.
4. **Support process-scoped proc paths** such as `proc/*/net/bonding/*`, `proc/*/net/softnet_stat`, `proc/*/mountstats` and `proc/*/mounts`.
5. **Netstate cannot depend on nmcli.** Use IP/ethtool and NetworkManager config/journal fallbacks.
6. **Chrony grading needs health, not just configuration.** Track configured count, reachable count, selected source and synchronization state separately.
7. **Kdump does not require `kdumpctl_status`.** systemd state + crashkernel + reserved memory + kdump.conf + sysctl form the core evidence set.
8. **Parser returns facts only.** Applicability and A/B/C remain rule-engine responsibilities.
9. **Missing evidence after all candidates resolve to nothing/error becomes internal `SKIPPED`.** It is never rendered as customer-visible UNKNOWN.
10. **Evidence should retain the actual resolved sosreport path and parser note** (including command-error content when relevant) so report generation and troubleshooting are traceable.

## Regression fixture strategy

Do not commit complete customer sosreports into normal unit tests. Build reduced/sanitized fixture directories containing only required source files. At minimum create fixtures for:

- `boot_uefi_rhel8`, `boot_uefi_rhel9`, `boot_legacy_efibootmgr_missing_binary`.
- `chrony_4_sources_ok`, `chrony_2_sources_ok`, `chrony_2_sources_unreachable`, `chrony_1_source`.
- `bond_none`, `bond_1`, `bond_2`, `bond_3`, `bond_4`.
- `multipath_active`, `multipath_zero_maps`, `multipath_driver_not_loaded`.
- `nfs_present`, `nfs_absent_but_plugin_collected`.
- `tuned_network_latency`, `tuned_throughput_performance`, `tuned_sap_netweaver`, `tuned_sap_hana`, `tuned_daemon_not_running`.
- `sysstat_present`, `sysstat_absent`.
- `netstate_with_nmcli`, `netstate_without_nmcli`.
