from sosdiag.diagnostics.selinux import evaluate_selinux
from sosdiag.model.facts import SelinuxFacts


def test_rhel8_disabled_is_pass():
    result = evaluate_selinux(
        SelinuxFacts(
            rhel_major=8,
            runtime_mode="Disabled",
            configured_mode="Disabled",
            runtime_config_mismatch=False,
            runtime_source="getenforce",
            configured_source="/etc/selinux/config",
        )
    )

    assert result.status == "PASS"
    assert result.current_values["runtime_mode"] == "Disabled"


def test_rhel8_enforcing_is_warn():
    result = evaluate_selinux(
        SelinuxFacts(
            rhel_major=8,
            runtime_mode="Enforcing",
            configured_mode="Enforcing",
            runtime_config_mismatch=False,
        )
    )

    assert result.status == "WARN"


def test_rhel9_selinux_zero_is_pass():
    result = evaluate_selinux(
        SelinuxFacts(
            rhel_major=9,
            runtime_mode="Disabled",
            configured_mode="Disabled",
            kernel_cmdline="BOOT_IMAGE=/vmlinuz root=/dev/mapper/root ro selinux=0",
            kernel_selinux_disabled=True,
            kernel_cmdline_source="/proc/cmdline",
        )
    )

    assert result.status == "PASS"
    assert result.current_values["kernel_selinux_disabled"] is True


def test_rhel9_without_selinux_zero_is_warn_even_if_config_disabled():
    result = evaluate_selinux(
        SelinuxFacts(
            rhel_major=9,
            runtime_mode="Permissive",
            configured_mode="Disabled",
            runtime_config_mismatch=True,
            kernel_cmdline="BOOT_IMAGE=/vmlinuz root=/dev/mapper/root ro quiet",
            kernel_selinux_disabled=False,
            kernel_cmdline_source="/proc/cmdline",
        )
    )

    assert result.status == "WARN"
    assert any("selinux=0" in finding for finding in result.findings)


def test_rhel9_missing_cmdline_is_skipped():
    result = evaluate_selinux(
        SelinuxFacts(
            rhel_major=9,
            runtime_mode="Disabled",
            configured_mode="Disabled",
        )
    )

    assert result.status == "SKIPPED"
    assert result.include_in_report is False


def test_runtime_config_mismatch_is_reported():
    result = evaluate_selinux(
        SelinuxFacts(
            rhel_major=8,
            runtime_mode="Permissive",
            configured_mode="Disabled",
            runtime_config_mismatch=True,
        )
    )

    assert result.status == "WARN"
    assert any("일치하지 않습니다" in finding for finding in result.findings)


def test_missing_os_version_is_skipped():
    result = evaluate_selinux(SelinuxFacts(runtime_mode="Disabled"))

    assert result.status == "SKIPPED"
    assert result.include_in_report is False
