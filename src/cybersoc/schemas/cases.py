from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from cybersoc.schemas.events import AgentFinding, Evidence, Severity


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TimelineEntry(Contract):
    timestamp: datetime
    event_type: str
    evidence_id: str


class CaseReport(Contract):
    schema_version: Literal["1.0"] = "1.0"
    case_id: str
    scenario: str
    severity: Severity
    summary: str
    evidence: list[Evidence] = Field(min_length=1)
    findings: list[AgentFinding]
    timeline: list[TimelineEntry]
    limitations: list[str]
    recommendations: list[str]
    playbook: str

    @model_validator(mode="after")
    def validate_evidence_links(self):
        available = {item.evidence_id for item in self.evidence}
        if len(available) != len(self.evidence):
            raise ValueError("duplicate evidence records")
        linked = {ref for item in self.findings for ref in item.evidence_ids}
        linked.update(item.evidence_id for item in self.timeline)
        if not linked <= available:
            raise ValueError("case references unknown evidence")
        return self


class AgentTrace(Contract):
    trace_id: str
    case_id: str
    agent: str
    version: Literal["1.0"] = "1.0"
    duration_ms: float = Field(ge=0)
    tools: list[str]
    input_evidence_ids: list[str]
    output_evidence_ids: list[str]
    status: Literal["ok", "failed", "timeout"]
    retries: int = Field(default=0, ge=0)
    error_class: str | None = None


class CaseRun(Contract):
    status: Literal["reported", "manual_review"]
    case_id: str
    trace_id: str
    report: CaseReport | None
    traces: list[AgentTrace]
