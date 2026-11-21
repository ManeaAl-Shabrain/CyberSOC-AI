import json
from datetime import UTC, datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, field_validator, model_validator


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class SecurityEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(min_length=1, max_length=100)
    timestamp: datetime
    source: str = Field(min_length=1, max_length=100)
    event_type: str = Field(min_length=1, max_length=100)
    asset_id: str = Field(min_length=1, max_length=100)
    raw_data: dict[str, JsonValue] = Field(default_factory=dict)
    simulation: Literal[True] = True

    @field_validator("raw_data")
    @classmethod
    def bounded_json(cls, value: dict[str, JsonValue]) -> dict[str, JsonValue]:
        if len(json.dumps(value, ensure_ascii=True, allow_nan=False).encode()) > 12_000:
            raise ValueError("raw_data exceeds size limit")
        return value

    @field_validator("timestamp")
    @classmethod
    def utc_only(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
            raise ValueError("timestamp must be UTC")
        return value

class Evidence(BaseModel):
    evidence_id: str
    event_id: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source: str

class AgentFinding(BaseModel):
    agent_id: str
    statement: str
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    unverified: bool = False

    @field_validator("evidence_ids")
    @classmethod
    def no_duplicates(cls, ids: list[str]) -> list[str]:
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate evidence IDs")
        return ids

    @model_validator(mode="after")
    def require_evidence_or_uncertainty(self):
        if not self.evidence_ids and not self.unverified:
            raise ValueError("findings without evidence must be unverified")
        return self
