from __future__ import annotations

from pydantic import BaseModel, Field


class TunedFacts(BaseModel):
    enabled: bool | None = None
    active: bool | None = None
    active_profile: str | None = None
    recommended_profile: str | None = None
    host_type: str | None = None
    live_10g: bool | None = None
    evidence_paths: list[str] = Field(default_factory=list)


class IrqbalanceFacts(BaseModel):
    enabled: bool | None = None
    active: bool | None = None
    oneshot: str | None = None
    evidence_paths: list[str] = Field(default_factory=list)


class TimerFacts(BaseModel):
    enabled: bool | None = None
    active: bool | None = None
    listed: bool | None = None
    evidence_paths: list[str] = Field(default_factory=list)


class OtherSettingsFacts(BaseModel):
    rsyslog_filter_present: bool | None = None
    cron_mailto: str | None = None
    cron_mailto_present: bool | None = None
    evidence_paths: list[str] = Field(default_factory=list)
