import pytest
from pydantic import ValidationError

from cybersoc.orchestration import agents
from cybersoc.orchestration.workflow import TransientToolError, run_case
from cybersoc.scenarios import dataset, synthetic_case
from cybersoc.schemas.cases import CaseReport


@pytest.mark.parametrize("scenario", dataset().scenarios, ids=lambda item: item.id)
def test_end_to_end(scenario):
    run = run_case(scenario)
    assert run.status == "reported"
    assert run.report == run_case(scenario).report
    assert run.report.severity == scenario.expected
    assert [trace.agent for trace in run.traces] == ["intake", "enrichment", "detection", "triage", "investigation", "reporting"]
    assert all(trace.trace_id == run.trace_id and trace.status == "ok" for trace in run.traces)
    assert "DEMO UNTRUSTED TEXT" not in run.model_dump_json()


def test_dangling_evidence_is_rejected():
    report = run_case(synthetic_case("routine-sign-in")).report.model_dump()
    report["timeline"][0]["evidence_id"] = "invented"
    with pytest.raises(ValidationError, match="unknown evidence"):
        CaseReport.model_validate(report)


def test_transient_retry_and_failure_redaction(monkeypatch):
    original = agents.enrich
    attempts = []

    def flaky(scenario):
        attempts.append(scenario.id)
        if len(attempts) == 1:
            raise TransientToolError("internal details")
        return original(scenario)

    monkeypatch.setattr(agents, "enrich", flaky)
    run = run_case(synthetic_case("routine-sign-in"))
    assert run.traces[1].retries == 1
    assert run.status == "reported"

    def unavailable(_):
        raise TransientToolError("internal details")

    monkeypatch.setattr(agents, "enrich", unavailable)
    failed = run_case(synthetic_case("routine-sign-in"))
    assert failed.status == "manual_review" and failed.report is None
    assert failed.traces[-1].retries == 1 and failed.traces[-1].status == "failed"
    assert "internal details" not in failed.model_dump_json()


def test_exhausted_budget_routes_to_manual_review():
    run = run_case(synthetic_case("routine-sign-in"), budget_ms=0)
    assert run.status == "manual_review"
    assert run.traces[0].status == "timeout"
