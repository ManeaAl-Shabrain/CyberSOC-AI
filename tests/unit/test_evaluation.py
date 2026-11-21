from cybersoc.evaluation import evaluate


def test_regression_gate():
    result = evaluate()
    assert len(result.cases) == 8
    assert result.passed
    assert result.severity_agreement == result.precision == result.recall == result.grounded_link_rate == 1
    assert all(case.redaction and case.tools_allowed and case.evidence_integrity for case in result.cases)
    assert 0 <= result.p50_ms <= result.p95_ms
    assert result.model_tokens == 0


def test_negative_control_demonstrates_gate_failure(monkeypatch, capsys):
    from cybersoc import evaluation
    from cybersoc.orchestration import agents
    from cybersoc.schemas.events import Severity

    monkeypatch.setattr(agents, "triage", lambda *_arguments: Severity.low)
    assert evaluation.main() == 1
    assert '"passed": false' in capsys.readouterr().out
