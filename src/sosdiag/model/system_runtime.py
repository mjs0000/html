from __future__ import annotations

from pydantic import BaseModel, Field


class PackageUpdateFacts(BaseModel):
    rhel_major: int | None = None
    architecture: str | None = None
    running_kernel: str | None = None
    installed_kernels: list[str] = Field(default_factory=list)
    newest_installed_kernel: str | None = None
    reference_version: str | None = None
    reference_source: str | None = None
    reference_url: str | None = None
    evidence_paths: list[str] = Field(default_factory=list)


class FirewalldFacts(BaseModel):
    enabled: bool | None = None
    active: bool | None = None
    default_zone: str | None = None
    zones_text: str | None = None
    evidence_paths: list[str] = Field(default_factory=list)


class ChronyFacts(BaseModel):
    active: bool | None = None
    configured_source_count: int | None = None
    evidence_paths: list[str] = Field(default_factory=list)


class KdumpFacts(BaseModel):
    enabled: bool | None = None
    active: bool | None = None
    crashkernel_parameter: str | None = None
    kexec_crash_size: int | None = None
    kdumpctl_showmem: str | None = None
    parameters: dict[str, int | str | None] = Field(default_factory=dict)
    evidence_paths: list[str] = Field(default_factory=list)
