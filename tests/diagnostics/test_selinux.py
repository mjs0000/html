from sosdiag.diagnostics.selinux import evaluate_selinux
from sosdiag.model.facts import SelinuxFacts


def test_disabled_is_grade_a():
    result = evaluate_selinux(
        SelinuxFacts(
            runtime_mode="Disabled",
            configured_mode="Disabled",
            runtime_config_mismatch=False,
            runtime_source="getenforce",
            configured_source="/etc/selinux/config",
        )
    )

    assert result.status == "PASS"
    assert result.grade == "A"
    assert result.current_values["runtime_mode"] == "Disabled"
    assert result.recommended_values["state"] == "disabled"


def test_enforcing_is_grade_b_and_current_state_visible():
    result = evaluate_selinux(
        SelinuxFacts(
            runtime_mode="Enforcing",
            configured_mode="Enforcing",
            runtime_config_mismatch=False,
        )
    )

    assert result.status == "WARN"
    assert result.grade == "B"
    assert result.current_values["runtime_mode"] == "Enforcing"


def test_mismatch_is_reported():
    result = evaluate_selinux(
        SelinuxFacts(
            runtime_mode="Permissive",
            configured_mode="Disabled",
            runtime_config_mismatch=True,
        )
    )

    assert result.grade == "B"
    assert any("일치하지 않습니다" in finding for finding in result.findings)


def test_missing_evidence_is_skipped():
    result = evaluate_selinux(SelinuxFacts())

    assert result.status == "SKIPPED"
    assert result.grade is None
    assert result.include_in_report is False
