from collections.abc import Callable
from dataclasses import dataclass
from time import perf_counter
from typing import TypeVar
from uuid import uuid4

from cybersoc.orchestration import agents
from cybersoc.scenarios import Scenario
from cybersoc.schemas.cases import AgentTrace, CaseRun
from cybersoc.schemas.events import SecurityEvent, Severity


class TransientToolError(RuntimeError):
    """A local, read-only stage can safely be attempted once more."""


class StageFailure(RuntimeError):
    """Workflow stage failed and produced a redacted trace."""


Result = TypeVar("Result")


@dataclass(frozen=True)
class AdvisoryStages:
    triage: Callable[[list[SecurityEvent], tuple[SecurityEvent, ...], agents.Enrichment], tuple[Severity, list[str]]]
    investigate: Callable[[list[SecurityEvent]], agents.Investigation]


def run_case(scenario: Scenario, *, budget_ms: float = 2_000, advisory: AdvisoryStages | None = None) -> CaseRun:
    case_id = f"case:{scenario.id}"
    trace_id = uuid4().hex
    traces: list[AgentTrace] = []
    deadline = perf_counter() + budget_ms / 1_000

    def stage(name: str, tools: list[str], incoming: list[str], operation: Callable[[], Result],
              outgoing: Callable[[Result], list[str]]) -> Result:
        started = perf_counter()
        status = "failed"
        error_class = None
        outputs: list[str] = []
        retries = 0
        try:
            if started >= deadline:
                raise TimeoutError
            try:
                result = operation()
            except TransientToolError:
                if perf_counter() >= deadline:
                    raise TimeoutError from None
                retries = 1
                result = operation()
            if perf_counter() >= deadline:
                raise TimeoutError
            outputs = outgoing(result)
            status = "ok"
            return result
        except Exception as exc:
            status = "timeout" if isinstance(exc, TimeoutError) else "failed"
            error_class = type(exc).__name__
            raise StageFailure from exc
        finally:
            traces.append(AgentTrace(
                trace_id=trace_id, case_id=case_id, agent=name, duration_ms=(perf_counter() - started) * 1_000,
                tools=tools, input_evidence_ids=incoming, output_evidence_ids=outputs,
                status=status, retries=retries, error_class=error_class,
            ))

    try:
        events = stage("intake", ["synthetic-fixture", "event-schema"], [], lambda: agents.intake(scenario), agents.refs)
        event_ids = agents.refs(events)
        context = stage("enrichment", ["synthetic-inventory", "synthetic-change-log"], event_ids,
                        lambda: agents.enrich(scenario), lambda result: agents.refs(result.records))
        context_ids = agents.refs(context.records)
        cluster = stage("detection", ["sign-in-correlation"], event_ids, lambda: agents.detect(events), agents.refs)
        signal_ids = agents.refs(cluster)
        all_ids = [*event_ids, *context_ids]
        local_inputs = [*signal_ids, *context_ids]
        severity, _ = stage(
            "triage", ["foundry", "evidence-validator"] if advisory else ["severity-rubric"],
            all_ids if advisory else local_inputs,
            lambda: advisory.triage(events, cluster, context) if advisory else (agents.triage(cluster, context), local_inputs),
            lambda decision: decision[1],
        )
        findings = stage(
            "investigation", ["foundry", "timeline-builder"] if advisory else ["timeline-builder"], all_ids,
            lambda: advisory.investigate(events) if advisory else agents.investigate(events, cluster, context),
            lambda result: sorted({ref for finding in result.findings for ref in finding.evidence_ids}),
        )
        result = stage("reporting", ["approved-playbook", "case-validator"], [*event_ids, *context_ids],
                       lambda: agents.report(case_id, scenario, events, context, severity, findings),
                       lambda report: [item.evidence_id for item in report.evidence])
    except StageFailure:
        return CaseRun(status="manual_review", case_id=case_id, trace_id=trace_id, report=None, traces=traces)

    return CaseRun(status="reported", case_id=case_id, trace_id=trace_id, report=result, traces=traces)
