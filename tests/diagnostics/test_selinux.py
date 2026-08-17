from sosdiag.diagnostics.selinux import evaluate_selinux
from sosdiag.model.facts import SelinuxFacts


def test_disabled_primary_evidence_is_pass():
    result = evaluate_selinux(
        SelinuxFacts(
            rhel_major=9,
            runtime_mode="Disabled",
            configured_mode="Disabled",
            runtime_config_mismatch=False,
            runtime_source="getenforce",
            configured_source="/etc/selinux/config",
        )
    )

    assert result.status == "PASS"
    assert result.current_values["runtime_mode"] == "Disabled"


def test_enforcing_primary_evidence_is_warn():
    result = evaluate_selinux(
        SelinuxFacts(
            rhel_major=9,
            runtime_mode="Enforcing",
            configured_mode="Enforcing",
            runtime_config_mismatch=False,
        )
    )

    assert result.status == "WARN"


def test_rhel9_selinux_zero_is_supporting_evidence():
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


def test_rhel9_without_selinux_zero_is_normal_when_primary_evidence_is_disabled():
    result = evaluate_selinux(
        SelinuxFacts(
            rhel_major=9,
            runtime_mode="Disabled",
            configured_mode="Disabled",
            runtime_config_mismatch=False,
            kernel_cmdline="BOOT_IMAGE=/vmlinuz root=/dev/mapper/root ro quiet",
            kernel_selinux_disabled=False,
            kernel_cmdline_source="/proc/cmdline",
        )
    )

    assert result.status == "PASS"
    assert result.findings == []


def test_rhel9_missing_cmdline_does_not_skip_when_primary_evidence_exists():
    result = evaluate_selinux(
        SelinuxFacts(
            rhel_major=9,
            runtime_mode="Disabled",
            configured_mode="Disabled",
        )
    )

    assert result.status == "PASS"
    assert result.include_in_report is True


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


def test_single_primary_source_can_be_used_with_missing_evidence_finding():
    result = evaluate_selinux(
        SelinuxFacts(
            rhel_major=9,
            runtime_mode="Disabled",
            configured_mode=None,
        )
    )

    assert result.status == "PASS"
    assert any("/etc/selinux/config" in finding for finding in result.findings)


def test_missing_both_primary_sources_is_skipped():
    result = evaluate_selinux(SelinuxFacts(rhel_major=9))

    assert result.status == "SKIPPED"
    assert result.include_in_report is False
