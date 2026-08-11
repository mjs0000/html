from typing import Any, Literal

from pydantic import BaseModel, Field

Grade = Literal["A", "B", "C"]
InternalStatus = Literal["PASS", "WARN", "FAIL", "SKIPPED"]


class Evidence(BaseModel):
    source: str
    detail: str


class ReportTable(BaseModel):
    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)


class DiagnosticResult(BaseModel):
    id: str
    category: str
    section: str
    title: str
    status: InternalStatus
    grade: Grade | None = None
    value: str | None = None
    definition: str | None = None
    summary: str | None = None
    findings: list[str] = Field(default_factory=list)
    current_values: dict[str, Any] = Field(default_factory=dict)
    recommended_values: dict[str, Any] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)
    remediation: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    tables: list[ReportTable] = Field(default_factory=list)
    include_in_report: bool = True


class HostReport(BaseModel):
    hostname: str
    system_type: str | None = None
    hardware_model: str | None = None
    os_version: str | None = None
    diagnostics: list[DiagnosticResult] = Field(default_factory=list)

    def reportable_diagnostics(self) -> list[DiagnosticResult]:
        return [
            item
            for item in self.diagnostics
            if item.include_in_report and item.status != "SKIPPED" and item.grade is not None
        ]
