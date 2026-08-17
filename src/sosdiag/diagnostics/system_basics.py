from __future__ import annotations

from sosdiag.model.diagnostic import DiagnosticResult, Evidence, ReportTable
from sosdiag.model.system_basics import BootModeFacts, FilesystemFacts, HardwareCertificationFacts, LifecycleFacts


def evaluate_hardware_certification(facts: HardwareCertificationFacts) -> DiagnosticResult:
    evidence = [Evidence(source=path, detail="hardware identification evidence") for path in facts.evidence_paths]
    current_values = {
        "host_type": facts.host_type,
        "manufacturer": facts.manufacturer,
        "product_name": facts.product_name,
        "rhel_version": facts.rhel_version,
        "virtualization": facts.virtualization,
        "reference_name": facts.reference_name,
        "reference_url": facts.reference_url,
        "certification_scope": facts.certification_scope,
        "certification_confirmed": facts.certification_confirmed,
    }

    if not facts.manufacturer and not facts.product_name:
        return DiagnosticResult(
            id="SYS_HW_CERT",
            category="System",
            section="3.1",
            title="Hardware Certification",
            status="SKIPPED",
            summary="H/W 제조사/모델을 식별할 충분한 Evidence가 없어 Red Hat Hardware Certification을 판정할 수 없습니다.",
            current_values=current_values,
            evidence=evidence,
            include_in_report=True,
        )

    if facts.certification_confirmed is True:
        return DiagnosticResult(
            id="SYS_HW_CERT",
            category="System",
            section="3.1",
            title="Hardware Certification",
            status="PASS",
            summary="구성된 외부 Red Hat Hardware Certification reference에서 해당 H/W/RHEL 조합을 확인했습니다.",
            current_values=current_values,
            evidence=evidence,
        )

    if facts.certification_confirmed is False:
        return DiagnosticResult(
            id="SYS_HW_CERT",
            category="System",
            section="3.1",
            title="Hardware Certification",
            status="WARN",
            summary="구성된 외부 Red Hat Hardware Certification reference에서 해당 H/W/RHEL 조합을 확인하지 못했습니다. 미조회 상태만으로 FAIL 처리하지 않습니다.",
            current_values=current_values,
            evidence=evidence,
        )

    platform = "VM" if (facts.host_type or "").lower() == "virtual" else "Physical"
    return DiagnosticResult(
        id="SYS_HW_CERT",
        category="System",
        section="3.1",
        title="Hardware Certification",
        status="SKIPPED",
        summary=(
            f"{platform} H/W 식별 정보는 수집했으나 Red Hat Hardware Certification reference provider가 구성되지 않아 인증 여부를 판정하지 않았습니다."
        ),
        current_values=current_values,
        recommendations=["Red Hat Hardware Certification 공식 reference와 H/W Model/RHEL major 조합을 대조하십시오."],
        evidence=evidence,
        include_in_report=True,
    )


def evaluate_lifecycle(facts: LifecycleFacts) -> DiagnosticResult:
    evidence = [Evidence(source=path, detail=f"rhel_version={facts.rhel_version}") for path in facts.evidence_paths]
    if facts.rhel_major is None:
        return DiagnosticResult(
            id="SYS_LIFECYCLE",
            category="System",
            section="3.2",
            title="Life-Cycle",
            status="SKIPPED",
            summary="RHEL major version을 확인할 수 없습니다.",
            include_in_report=False,
            evidence=evidence,
        )
    status = "PASS" if facts.rhel_major in {8, 9} else "SKIPPED"
    return DiagnosticResult(
        id="SYS_LIFECYCLE",
        category="System",
        section="3.2",
        title="Life-Cycle",
        status=status,
        value=f"RHEL {facts.rhel_major}",
        summary=(
            "프로젝트 기준에서 RHEL major version 지원 범위에 포함됩니다."
            if status == "PASS"
            else "현재 프로젝트에서 평가 가능한 RHEL major version 범위를 벗어납니다."
        ),
        current_values={"rhel_version": facts.rhel_version, "rhel_major": facts.rhel_major},
        recommended_values={"supported_major_versions": [8, 9]},
        evidence=evidence,
        include_in_report=status != "SKIPPED",
    )


def evaluate_boot_mode(facts: BootModeFacts) -> DiagnosticResult:
    evidence = [Evidence(source=path, detail=f"boot_mode={facts.mode}") for path in facts.evidence_paths]
    if facts.mode is None:
        return DiagnosticResult(
            id="SYS_BOOT_MODE",
            category="System",
            section="3.3",
            title="Boot Mode",
            status="SKIPPED",
            summary="UEFI/BIOS를 판정할 충분한 Evidence가 없습니다.",
            include_in_report=False,
            evidence=evidence,
        )
    status = "PASS" if facts.mode == "UEFI" else "WARN"
    return DiagnosticResult(
        id="SYS_BOOT_MODE",
        category="System",
        section="3.3",
        title="Boot Mode",
        status=status,
        value=facts.mode,
        summary="UEFI 권고 상태입니다." if status == "PASS" else "BIOS Legacy Mode로 확인되어 UEFI 권고 기준과 다릅니다.",
        current_values=facts.model_dump(),
        recommended_values={"boot_mode": "UEFI"},
        evidence=evidence,
    )


def evaluate_filesystem(facts: FilesystemFacts) -> DiagnosticResult:
    if not facts.entries:
        return DiagnosticResult(
            id="SYS_FILESYSTEM",
            category="System",
            section="3.4",
            title="Filesystem",
            status="SKIPPED",
            summary="Filesystem Type/LVM을 평가할 마운트 Evidence가 없습니다.",
            include_in_report=False,
            evidence=[Evidence(source=path, detail="filesystem evidence") for path in facts.evidence_paths],
        )

    rows = []
    statuses: list[str] = []
    findings: list[str] = []
    for entry in facts.entries:
        fs_status = "PASS" if (entry.filesystem_type or "").lower() == "xfs" else "WARN"
        lvm_status = "SKIPPED" if entry.lvm is None else ("PASS" if entry.lvm else "WARN")
        row_status = "WARN" if "WARN" in {fs_status, lvm_status} else ("PASS" if fs_status == lvm_status == "PASS" else "SKIPPED")
        statuses.append(row_status)
        rows.append(
            {
                "mount_point": entry.mount_point,
                "device": entry.device,
                "filesystem_type": entry.filesystem_type,
                "lvm": entry.lvm,
                "status": row_status,
            }
        )
        if fs_status == "WARN":
            findings.append(f"{entry.mount_point}: Filesystem Type이 XFS가 아닙니다 ({entry.filesystem_type}).")
        if lvm_status == "WARN":
            findings.append(f"{entry.mount_point}: LVM 구성이 확인되지 않습니다 ({entry.device}).")

    overall = "WARN" if "WARN" in statuses else ("PASS" if all(s == "PASS" for s in statuses) else "SKIPPED")
    return DiagnosticResult(
        id="SYS_FILESYSTEM",
        category="System",
        section="3.4",
        title="Filesystem",
        status=overall,
        summary="Filesystem Type과 LVM 구성만 프로젝트 기준으로 평가합니다.",
        findings=findings,
        recommended_values={"filesystem_type": "XFS", "lvm": True},
        evidence=[Evidence(source=path, detail="filesystem/lvm evidence") for path in facts.evidence_paths],
        tables=[
            ReportTable(
                columns=["mount_point", "device", "filesystem_type", "lvm", "status"],
                rows=rows,
            )
        ],
        include_in_report=overall != "SKIPPED",
    )
