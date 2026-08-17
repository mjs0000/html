from __future__ import annotations

from pydantic import BaseModel, Field


class HardwareCertificationFacts(BaseModel):
    host_type: str | None = None
    manufacturer: str | None = None
    product_name: str | None = None
    rhel_version: str | None = None
    virtualization: str | None = None
    reference_name: str | None = None
    reference_url: str | None = None
    certification_scope: str | None = None
    certification_confirmed: bool | None = None
    evidence_paths: list[str] = Field(default_factory=list)


class LifecycleFacts(BaseModel):
    rhel_version: str | None = None
    rhel_major: int | None = None
    evidence_paths: list[str] = Field(default_factory=list)


class BootModeFacts(BaseModel):
    mode: str | None = None
    direct_efi_present: bool | None = None
    firmware_listing_has_efi: bool | None = None
    efibootmgr_available: bool | None = None
    evidence_paths: list[str] = Field(default_factory=list)


class FilesystemEntry(BaseModel):
    mount_point: str
    device: str | None = None
    filesystem_type: str | None = None
    lvm: bool | None = None


class FilesystemFacts(BaseModel):
    entries: list[FilesystemEntry] = Field(default_factory=list)
    evidence_paths: list[str] = Field(default_factory=list)
