from collections import Counter
from math import ceil
from typing import Literal

from cybersoc.orchestration.workflow import run_case
from cybersoc.scenarios import context_records, dataset, evidence_for, generate_events
from cybersoc.schemas.cases import Contract
from cybersoc.schemas.events import Severity

TOOLS_BY_STAGE = {
    "intake": {"synthetic-fixture", "event-schema"},
    "enrichment": {"synthetic-inventory", "synthetic-change-log"},
    "detection": {"sign-in-correlation"},
    "triage": {"severity-rubric"},
    "investigation": {"timeline-builder"},
    "reporting": {"approved-playbook", "case-validator"},
}
POSITIVE = {Severity.medium, Severity.high, Severity.critical}


class EvaluationCase(Contract):
    scenario: str
    expected: Severity
    observed: Severity | None
    evidence_integrity: bool
    grounded_links: bool
    task_adherence: bool
    tools_allowed: bool
    redaction: bool
    duration_ms: float
    passed: bool


class EvaluationResult(Contract):
    dataset_version: str
    scope: Literal["offline-synthetic"] = "offline-synthetic"
    cases: list[EvaluationCase]
    severity_agreement: float
    precision: float
    recall: float
    grounded_link_rate: float
    p50_ms: float
    p95_ms: float
    model_tokens: Literal[0] = 0
    passed: bool


def evaluate() -> EvaluationResult:
    fixtures = dataset()
    cases: list[EvaluationCase] = []
    matrix: Counter[str] = Counter()
    for scenario in fixtures.scenarios:
        run = run_case(scenario)
        report = run.report
        observed = report.severity if report else None
        expected_evidence = {
            record.evidence_id: record
            for record in map(evidence_for, [*generate_events(scenario), *context_records(scenario)])
        }
        evidence = {item.evidence_id: item for item in report.evidence} if report else {}
        integrity = evidence == expected_evidence
        linked = bool(report and report.findings and all(
            bool(finding.evidence_ids) and set(finding.evidence_ids) <= evidence.keys() for finding in report.findings
        ))
        adherence = bool(report and report.timeline and report.recommendations and report.limitations and report.playbook
                         and run.status == "reported" and list(TOOLS_BY_STAGE) == [item.agent for item in run.traces])
        tooling = bool(run.traces) and all(
            set(item.tools) == TOOLS_BY_STAGE.get(item.agent) and item.status == "ok" for item in run.traces
        )
        redaction = not scenario.note or scenario.note not in run.model_dump_json()
        cases.append(EvaluationCase(
            scenario=scenario.id, expected=scenario.expected, observed=observed,
            evidence_integrity=integrity, grounded_links=linked, task_adherence=adherence,
            tools_allowed=tooling, redaction=redaction, duration_ms=sum(item.duration_ms for item in run.traces),
            passed=observed == scenario.expected and integrity and linked and adherence and tooling and redaction,
        ))
        if observed in POSITIVE:
            matrix["tp" if scenario.expected in POSITIVE else "fp"] += 1
        elif scenario.expected in POSITIVE:
            matrix["fn"] += 1

    timings = sorted(case.duration_ms for case in cases)
    return EvaluationResult(
        dataset_version=fixtures.version, cases=cases,
        severity_agreement=sum(case.observed == case.expected for case in cases) / len(cases),
        precision=matrix["tp"] / max(1, matrix["tp"] + matrix["fp"]),
        recall=matrix["tp"] / max(1, matrix["tp"] + matrix["fn"]),
        grounded_link_rate=sum(case.grounded_links for case in cases) / len(cases),
        p50_ms=timings[ceil(.50 * len(timings)) - 1],
        p95_ms=timings[ceil(.95 * len(timings)) - 1],
        passed=all(case.passed for case in cases),
    )


def main() -> int:
    result = evaluate()
    print(result.model_dump_json(indent=2))
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
