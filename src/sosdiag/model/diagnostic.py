from typing import Literal

from pydantic import BaseModel, Field

Grade = Literal["A", "B", "C", "UNKNOWN"]


class Evidence(BaseModel):
    source: str
    detail: str


class DiagnosticResult(BaseModel):
    id: str
    category: str
    section: str
    title: str
    grade: Grade
    value: str | None = None
    findings: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)


class HostReport(BaseModel):
    hostname: str
    os_version: str | None = None
    diagnostics: list[DiagnosticResult] = Field(default_factory=list)
