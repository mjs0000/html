from __future__ import annotations

import json
from pathlib import Path

import typer

from sosdiag.archive import SosArchive
from sosdiag.diagnostics.network_storage import (
    evaluate_bonding,
    evaluate_multipath,
    evaluate_netstate,
    evaluate_network_kernel,
)
from sosdiag.diagnostics.selinux import evaluate_selinux
from sosdiag.diagnostics.system_basics import evaluate_boot_mode, evaluate_filesystem, evaluate_lifecycle
from sosdiag.diagnostics.system_mid import (
    evaluate_coredump,
    evaluate_default_services,
    evaluate_error_log,
    evaluate_kernel_parameters,
    evaluate_logrotate_sysstat,
)
from sosdiag.diagnostics.system_runtime import evaluate_chrony, evaluate_firewalld, evaluate_kdump, evaluate_package_update
from sosdiag.diagnostics.system_tail import evaluate_irqbalance, evaluate_other_settings, evaluate_timer, evaluate_tuned
from sosdiag.parser.host import parse_host_facts
from sosdiag.parser.network_storage import (
    parse_bonding_facts,
    parse_multipath_facts,
    parse_netstate_facts,
    parse_network_kernel_facts,
)
from sosdiag.parser.selinux import parse_selinux
from sosdiag.parser.system_basics import (
    parse_boot_mode_facts,
    parse_filesystem_facts,
    parse_hardware_certification_facts,
    parse_lifecycle_facts,
)
from sosdiag.parser.system_mid import (
    parse_coredump_facts,
    parse_default_service_facts,
    parse_error_log_facts,
    parse_kernel_parameter_facts,
    parse_logrotate_sysstat_facts,
)
from sosdiag.parser.system_runtime import (
    parse_chrony_facts,
    parse_firewalld_facts,
    parse_kdump_facts,
    parse_package_update_facts,
)
from sosdiag.parser.system_tail import (
    parse_irqbalance_facts,
    parse_other_settings_facts,
    parse_timer_facts,
    parse_tuned_facts,
)

app = typer.Typer(help="Analyze RHEL sosreports and generate structure-diagnostic reports.")


def _text(archive: SosArchive, candidates: list[str]) -> str | None:
    found = archive.first_text(candidates)
    return found[1] if found else None


@app.command()
def analyze(
    source: str,
    format: str = typer.Option("html,docx", "--format"),
    output_dir: str = typer.Option("output", "--output-dir"),
) -> None:
    """Read a sosreport and emit normalized facts plus implemented diagnostics."""
    archive = SosArchive(source)
    host = parse_host_facts(archive)

    hardware = parse_hardware_certification_facts(host)
    lifecycle = evaluate_lifecycle(parse_lifecycle_facts(host))
    boot_mode = evaluate_boot_mode(parse_boot_mode_facts(archive))
    filesystem = evaluate_filesystem(parse_filesystem_facts(archive))
    package_update = evaluate_package_update(parse_package_update_facts(archive, host))

    selinux_sources = {
        "os_release": _text(archive, ["etc/redhat-release", "etc/os-release"]),
        "getenforce": _text(archive, ["sos_commands/selinux/getenforce"]),
        "sestatus": _text(archive, ["sos_commands/selinux/sestatus", "sos_commands/selinux/sestatus_-v"]),
        "config": _text(archive, ["etc/selinux/config"]),
        "cmdline": _text(archive, ["proc/cmdline"]),
    }
    selinux = evaluate_selinux(parse_selinux(selinux_sources))
    firewalld = evaluate_firewalld(parse_firewalld_facts(archive))
    chrony = evaluate_chrony(parse_chrony_facts(archive))
    kdump = evaluate_kdump(parse_kdump_facts(archive))

    error_log = evaluate_error_log(parse_error_log_facts(archive))
    kernel_params = evaluate_kernel_parameters(parse_kernel_parameter_facts(archive, host))
    default_services = evaluate_default_services(parse_default_service_facts(archive))
    coredump = evaluate_coredump(parse_coredump_facts(archive))
    logrotate_sysstat = evaluate_logrotate_sysstat(parse_logrotate_sysstat_facts(archive))

    tuned = evaluate_tuned(parse_tuned_facts(archive, host))
    irqbalance = evaluate_irqbalance(parse_irqbalance_facts(archive))
    timer = evaluate_timer(parse_timer_facts(archive))
    other_settings = evaluate_other_settings(parse_other_settings_facts(archive))

    bonding = evaluate_bonding(parse_bonding_facts(archive))
    network_kernel = evaluate_network_kernel(parse_network_kernel_facts(archive))
    netstate = evaluate_netstate(parse_netstate_facts(archive))
    multipath = evaluate_multipath(parse_multipath_facts(archive))

    diagnostics = [
        lifecycle,
        boot_mode,
        filesystem,
        package_update,
        selinux,
        firewalld,
        chrony,
        kdump,
        error_log,
        kernel_params,
        default_services,
        coredump,
        logrotate_sysstat,
        tuned,
        irqbalance,
        timer,
        other_settings,
        bonding,
        network_kernel,
        netstate,
        multipath,
    ]

    payload = {
        "host": host.model_dump(),
        "hardware_certification_facts": hardware.model_dump(),
        "diagnostics": [item.model_dump() for item in diagnostics],
    }

    outdir = Path(output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    output = outdir / "analysis.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    typer.echo(f"source={source}")
    typer.echo(f"requested_format={format}")
    typer.echo(f"analysis={output}")


if __name__ == "__main__":
    app()
