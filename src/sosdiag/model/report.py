from pydantic import BaseModel, Field

from .diagnostic import HostReport


class Person(BaseModel):
    name: str
    role: str | None = None
    phone: str | None = None
    email: str | None = None


class CustomerContact(Person):
    pass


class ReportInfo(BaseModel):
    title: str = "RHEL Health Check Report"
    version: str = "v0.1"
    report_date: str | None = None


class CustomerInfo(BaseModel):
    name: str
    site: str | None = None
    subscription: str | None = None
    contact: CustomerContact | None = None


class ExecutionPeriod(BaseModel):
    start: str | None = None
    end: str | None = None


class ExecutionInfo(BaseModel):
    period: ExecutionPeriod = Field(default_factory=ExecutionPeriod)
    location: str | None = None


class ReportMetadata(BaseModel):
    report: ReportInfo = Field(default_factory=ReportInfo)
    customer: CustomerInfo
    execution: ExecutionInfo = Field(default_factory=ExecutionInfo)
    sales_representative: Person | None = None
    technical_engineers: list[Person] = Field(default_factory=list)


class ReportRunError(BaseModel):
    source: str
    error: str


class IssueAggregate(BaseModel):
    warn_count: int = 0
    fail_count: int = 0
    hosts: list[str] = Field(default_factory=list)


class ReportRunSummary(BaseModel):
    source_count: int = 0
    analyzed_count: int = 0
    error_count: int = 0
    status_distribution: dict[str, dict[str, int]] = Field(default_factory=dict)
    issue_distribution: dict[str, dict[str, IssueAggregate]] = Field(default_factory=dict)
    errors: list[ReportRunError] = Field(default_factory=list)


class DiagnosticReport(BaseModel):
    metadata: ReportMetadata
    hosts: list[HostReport] = Field(default_factory=list)
    run_summary: ReportRunSummary | None = None
