from __future__ import annotations

from pydantic import BaseModel, Field


class EvidenceRef(BaseModel):
    path: str
    value: str | None = None


class HostFacts(BaseModel):
    hostname: str | None = None
    rhel_version: str | None = None
    rhel_major: int | None = None
    architecture: str | None = None
    kernel_release: str | None = None
    manufacturer: str | None = None
    product_name: str | None = None
    virtualization: str | None = None
    host_type: str | None = None
    evidence: list[EvidenceRef] = Field(default_factory=list)
