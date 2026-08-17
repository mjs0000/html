from sosdiag.diagnostics.system_basics import evaluate_hardware_certification
from sosdiag.model.system_basics import HardwareCertificationFacts


def test_hardware_certification_without_reference_is_skipped_but_reportable() -> None:
    result = evaluate_hardware_certification(
        HardwareCertificationFacts(
            host_type="physical",
            manufacturer="Dell Inc.",
            product_name="PowerEdge R760",
            rhel_version="9.6",
            evidence_paths=["sos_commands/hardware/dmidecode", "sos_commands/processor/lscpu"],
        )
    )

    assert result.id == "SYS_HW_CERT"
    assert result.status == "SKIPPED"
    assert result.include_in_report is True
    assert "reference provider" in (result.summary or "")


def test_hardware_certification_confirmed_is_pass() -> None:
    result = evaluate_hardware_certification(
        HardwareCertificationFacts(
            host_type="physical",
            manufacturer="Dell Inc.",
            product_name="PowerEdge R760",
            rhel_version="9.6",
            certification_confirmed=True,
            reference_name="Red Hat Ecosystem Catalog",
            reference_url="https://catalog.redhat.com/",
        )
    )

    assert result.status == "PASS"


def test_hardware_reference_negative_is_warn_not_fail() -> None:
    result = evaluate_hardware_certification(
        HardwareCertificationFacts(
            host_type="physical",
            manufacturer="Example Vendor",
            product_name="Example Server",
            rhel_version="9.6",
            certification_confirmed=False,
            reference_name="configured catalog snapshot",
        )
    )

    assert result.status == "WARN"
