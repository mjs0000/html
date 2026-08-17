from __future__ import annotations

from pydantic import BaseModel, Field


class ErrorFinding(BaseModel):
    source: str
    severity: str
    signature: str
    message: str
    count: int = 1
    timestamp: str | None = None
    component: str | None = None
    first_seen: str | None = None
    last_seen: str | None = None
    impact_category: str | None = None


class ErrorLogFacts(BaseModel):
    findings: list[ErrorFinding] = Field(default_factory=list)
    usable_sources: list[str] = Field(default_factory=list)


class KernelParameterFacts(BaseModel):
    values: dict[str, int | str | None] = Field(default_factory=dict)
    host_type: str | None = None
    nat_workload: bool | None = None
    evidence_paths: list[str] = Field(default_factory=list)


class ServiceState(BaseModel):
    enabled: bool | None = None
    active: bool | None = None


class DefaultServiceFacts(BaseModel):
    services: dict[str, ServiceState] = Field(default_factory=dict)
    evidence_paths: list[str] = Field(default_factory=list)


class CoreDumpFacts(BaseModel):
    hard_core_limit: str | None = None
    soft_core_limit: str | None = None
    limits_soft_unlimited: bool | None = None
    limits_hard_unlimited: bool | None = None
    default_limit_core: str | None = None
    retention_override: bool | None = None
    evidence_paths: list[str] = Field(default_factory=list)


class LogrotateSysstatFacts(BaseModel):
    logrotate_frequency: str | None = None
    logrotate_rotate_count: int | None = None
    sysstat_installed: bool | None = None
    sysstat_enabled: bool | None = None
    sar_interval_minutes: int | None = None
    evidence_paths: list[str] = Field(default_factory=list)
