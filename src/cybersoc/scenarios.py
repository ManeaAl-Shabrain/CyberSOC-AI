from datetime import UTC, datetime, timedelta
from importlib.resources import files
from typing import Literal

from pydantic import BaseModel, Field

from cybersoc.repositories.events import event_digest
from cybersoc.schemas.events import Evidence, SecurityEvent, Severity

DEMO_START = datetime(2026, 11, 21, 0, tzinfo=UTC)
AuthEvent = Literal["auth_failure", "auth_success", "mfa_fraud_report"]


class Scenario(BaseModel):
    id: str
    title: str
    asset: str
    change: Literal["approved", "none", "unknown"]
    privileged: bool
    events: list[tuple[AuthEvent, int]] = Field(min_length=1, max_length=100)
    expected: Severity
    note: str = ""


class Dataset(BaseModel):
    version: Literal["1.0"]
    scenarios: list[Scenario]


def dataset() -> Dataset:
    return Dataset.model_validate_json(files("cybersoc").joinpath("fixtures/scenarios.json").read_text(encoding="utf-8"))


def generate_events(scenario: Scenario) -> list[SecurityEvent]:
    return [
        SecurityEvent(
            event_id=f"{scenario.id}-{index:02}",
            timestamp=DEMO_START + timedelta(seconds=offset),
            source="synthetic-idp",
            event_type=event_type,
            asset_id=scenario.asset,
            raw_data={"note": scenario.note} if scenario.note and index == 1 else {},
        )
        for index, (event_type, offset) in enumerate(scenario.events, start=1)
    ]


def context_records(scenario: Scenario) -> list[SecurityEvent]:
    return [
        SecurityEvent(
            event_id=f"{scenario.id}-asset", timestamp=DEMO_START, source="synthetic-inventory",
            event_type="asset_profile", asset_id=scenario.asset, raw_data={"privileged": scenario.privileged},
        ),
        SecurityEvent(
            event_id=f"{scenario.id}-change", timestamp=DEMO_START, source="synthetic-change-log",
            event_type="change_status", asset_id=scenario.asset, raw_data={"status": scenario.change},
        ),
    ]


def evidence_for(event: SecurityEvent) -> Evidence:
    _, digest = event_digest(event)
    return Evidence(evidence_id=f"evidence:{event.event_id}", event_id=event.event_id, sha256=digest, source=event.source)


def synthetic_case(scenario_id: str) -> Scenario | None:
    return next((item for item in dataset().scenarios if item.id == scenario_id), None)
