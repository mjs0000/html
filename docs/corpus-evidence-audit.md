# 59-host sosreport evidence audit

This audit records evidence-path availability observed in the current 59-file sosreport corpus. Counts below describe collected evidence presence only; they are not diagnostic PASS/WARN distributions unless explicitly stated.

## Corpus

- Total sosreport archives: 59

## SELinux (3.6)

- `sos_commands/selinux/getenforce`: 0/59
- `sos_commands/selinux/sestatus` or `sestatus_-v`: 59/59
- `etc/selinux/config`: 59/59
- `proc/cmdline`: 59/59

Implication: `sestatus` must remain a supported runtime fallback because `getenforce` is not collected in this corpus.

## Time Sync / Chrony (3.8)

- `etc/chrony.conf`: 56/59
- `sos_commands/chrony/chronyc_-n_sources`: 56/59
- `sos_commands/chrony/chronyc_sources_-v`: 0/59

Implication: the parser must support `chronyc_-n_sources`; the older candidate name alone would cause excessive SKIPPED results.

## Kdump (3.9)

- `proc/cmdline`: 59/59
- `sys/kernel/kexec_crash_size`: 59/59
- `sos_commands/kdump/kdumpctl_showmem`: 0/59
- `sos_commands/systemd/systemctl_list-unit-files`: 59/59
- systemd unit list evidence: 59/59
- `sos_commands/kernel/sysctl_-a`: 59/59

Implication: `kdumpctl showmem` is optional display/supporting evidence in the current corpus and must not be mandatory for applicability or PASS by itself.

## Bonding (4.1)

- Hosts with real `/proc/*/net/bonding/*` evidence: 33/59
- Common actual path form: `proc/<pid>/net/bonding/<bond>`

Implication: a parser limited to `proc/net/bonding/*` misses real bonding data. The parser now accepts both `proc/net/bonding/*` and `proc/*/net/bonding/*`.

## NetworkManager / Netstate (4.2, 4.3)

- `nmcli_dev` / equivalent: 54/59
- active connection evidence: 54/59
- ethtool evidence: 59/59

The ethtool directory contains both direct interface output and many option-specific files such as `ethtool_-S_<iface>`, `ethtool_-i_<iface>`, and `ethtool_--phy-statistics_<iface>`. Direct link/speed parsing must ignore option-specific files.

## Multipath (5.1)

Evidence collection paths:

- `sos_commands/multipath/multipath_-ll`: 58/59
- `sos_commands/multipath/multipath_-v4_-ll`: 58/59
- `sos_commands/multipath/multipath_-t`: 58/59
- `sos_commands/multipath/multipathd_show_config`: 58/59

The existence of these command-output files does not imply a real multipath map. Applicability remains based on a parsed real map from `multipath -ll` or equivalent evidence.

A prior content-level check of the current corpus confirmed six hosts with real maps. Each observed host had two maps with four paths per map and no failed path in the sampled map/path state review. Do not generalize this into future corpus status counts without rerunning the content-level validation.

## Parser consistency

- `NET_KERNEL_PARAM` parser name is standardized as `network_sysctl` in both `spec/catalog.yaml` and `spec/rules/network/kernel-parameter.yaml`.

## Audit rule

Evidence-presence counts are safe to use for parser/path validation. Diagnostic status distributions must only be recorded after content-level parsing has completed successfully across the corpus. Timeouts or partial scans must not be converted into inferred 59-host PASS/WARN/SKIPPED totals.
