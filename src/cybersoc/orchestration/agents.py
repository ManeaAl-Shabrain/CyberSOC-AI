from dataclasses import dataclass

from cybersoc.correlation import correlate, severity_for
from cybersoc.scenarios import Scenario, context_records, evidence_for, generate_events
from cybersoc.schemas.cases import CaseReport, TimelineEntry
from cybersoc.schemas.events import AgentFinding, SecurityEvent, Severity

PLAYBOOK = "SOC-SIGN-IN v1.0"


def refs(events: list[SecurityEvent] | tuple[SecurityEvent, ...]) -> list[str]:
    return [f"evidence:{event.event_id}" for event in events]


@dataclass(frozen=True)
class Enrichment:
    records: list[SecurityEvent]
    privileged: bool
    change: str


@dataclass(frozen=True)
class Investigation:
    findings: list[AgentFinding]
    timeline: list[TimelineEntry]
    limitations: list[str]


def intake(scenario: Scenario) -> list[SecurityEvent]:
    return generate_events(scenario)


def enrich(scenario: Scenario) -> Enrichment:
    records = context_records(scenario)
    return Enrichment(records, records[0].raw_data["privileged"] is True, str(records[1].raw_data["status"]))


def detect(events: list[SecurityEvent]) -> tuple[SecurityEvent, ...]:
    return correlate(events)


def triage(cluster: tuple[SecurityEvent, ...], context: Enrichment) -> Severity:
    return severity_for(cluster, context.privileged, context.change)


def investigate(events: list[SecurityEvent], cluster: tuple[SecurityEvent, ...], context: Enrichment) -> Investigation:
    if cluster:
        statement = "At least three sign-in failures preceded a success on the same synthetic asset within five minutes."
        evidence_ids = refs(cluster)
    else:
        statement = "The supplied records do not establish a failure-to-success cluster under the current five-minute rule."
        evidence_ids = refs(events)
    findings = [AgentFinding(agent_id="investigation", statement=statement, evidence_ids=evidence_ids, confidence=.9)]
    if cluster and context.privileged:
        findings.append(AgentFinding(agent_id="investigation", statement="Synthetic inventory marks the account as privileged.",
                                     evidence_ids=refs(context.records[:1]), confidence=1))
    if cluster and context.change in {"approved", "none"}:
        statement = ("The fixture lists an approved change." if context.change == "approved"
                     else "The synthetic change lookup returned no matching approved change.")
        findings.append(AgentFinding(agent_id="investigation", statement=statement,
                                     evidence_ids=refs(context.records[1:]), confidence=1))
    if any(event.event_type == "mfa_fraud_report" for event in cluster):
        reports = [event for event in cluster if event.event_type == "mfa_fraud_report"]
        findings.append(AgentFinding(agent_id="investigation", statement="The fixture contains a user-reported MFA fraud event.",
                                     evidence_ids=refs(reports), confidence=1))
    limitations = ["Synthetic records cover the supplied window only. Account compromise remains unconfirmed."]
    if context.change == "unknown":
        limitations.append("Change records are unavailable. Ask an analyst to verify the change window.")
    if any(event.raw_data.get("note") for event in events):
        limitations.append("Free-text log content is excluded from findings and tool inputs.")
    timeline = [TimelineEntry(timestamp=event.timestamp, event_type=event.event_type, evidence_id=refs([event])[0])
                for event in sorted(events, key=lambda item: (item.timestamp, item.event_id))]
    return Investigation(findings, timeline, limitations)


def report(case_id: str, scenario: Scenario, events: list[SecurityEvent], context: Enrichment,
           severity: Severity, investigation: Investigation) -> CaseReport:
    next_step = ("Escalate to Tier 2 and verify with the account owner via an approved channel."
                 if severity in {Severity.high, Severity.critical}
                 else "Review the supplied evidence and record the analyst disposition.")
    return CaseReport(
        case_id=case_id, scenario=scenario.id, severity=severity,
        summary=f"{scenario.title}. Sent for analyst review.",
        evidence=[evidence_for(event) for event in [*events, *context.records]],
        findings=investigation.findings, timeline=investigation.timeline, limitations=investigation.limitations,
        recommendations=[next_step, "Review the synthetic MFA and sign-in timeline."], playbook=PLAYBOOK,
    )
