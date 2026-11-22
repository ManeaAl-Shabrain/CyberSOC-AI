import json

import pytest

from cybersoc.foundry_demo import INVESTIGATION_AGENT, TRIAGE_AGENT, run_foundry_case


def test_foundry_case_passes_triage_evidence_and_omits_untrusted_notes():
    calls = []

    def invoke(name, input_text):
        payload = json.loads(input_text)
        calls.append((name, payload))
        assert "raw_data" not in input_text and "expected" not in input_text
        ids = [payload["evidence"][0]["evidence_id"]]
        if name == TRIAGE_AGENT:
            return json.dumps({"severity": "high", "reason": "Synthetic sign-in signal.", "evidence_ids": ids})
        return json.dumps({"summary": "Review the sign-in.", "limitations": ["Simulated"],
                           "evidence_ids": ids, "next_step": "Ask an analyst to confirm the sign-in."})

    result = run_foundry_case("untrusted-log", invoke)
    assert [name for name, _ in calls] == [TRIAGE_AGENT, INVESTIGATION_AGENT]
    assert "triage" not in calls[0][1]
    assert calls[1][1]["triage"]["severity"] == "high"
    assert result["status"] == "reported"
    assert result["human_review_required"] is True
    assert result["report"]["findings"][0]["unverified"] is True
    assert result["report"]["severity"] == "high"
    assert result["report"]["recommendations"][0].endswith(result["investigation"]["next_step"])
    assert [stage["agent"] for stage in result["stages"]] == [
        "intake", "enrichment", "detection", "triage", "investigation", "reporting",
    ]
    assert all(stage["trace_id"] == result["trace_id"] for stage in result["stages"])


def test_invalid_evidence_stops_handoff():
    calls = []

    def invoke(name, _input_text):
        calls.append(name)
        return '{"severity":"high","reason":"Unverified.","evidence_ids":["invented"]}'

    result = run_foundry_case("privileged-sign-in", invoke)
    assert result["status"] == "manual_review"
    assert result["report"] is result["triage"] is result["investigation"] is None
    assert result["stages"][-1]["agent"] == "triage"
    assert result["stages"][-1]["error_class"] == "ValueError"
    assert calls == [TRIAGE_AGENT]


@pytest.mark.parametrize("model,tools", [
    ("gpt-6-luna", []),
    ("gpt-4.1-mini", ["toolbox"]),
])
def test_live_replay_rejects_agent_configuration(monkeypatch, model, tools):
    from contextlib import nullcontext
    from types import SimpleNamespace
    from unittest.mock import Mock

    from cybersoc import foundry_demo

    settings = foundry_demo.FoundrySettings("https://demo.services.ai.azure.com/api/projects/demo", "3", "4")
    project = Mock()
    project.agents.get_version.return_value = SimpleNamespace(
        definition=SimpleNamespace(model=model, tools=tools)
    )
    with_client = Mock()
    project.get_openai_client.return_value = nullcontext(with_client)
    monkeypatch.setattr(foundry_demo, "project_client", lambda _endpoint: nullcontext(project))

    with pytest.raises(RuntimeError, match="configured deployment with no tools"):
        foundry_demo.run_live_case(settings, "privileged-sign-in")

    project.agents.get_version.assert_called_once_with(agent_name=TRIAGE_AGENT, agent_version="3")
    with_client.with_options.assert_not_called()


@pytest.mark.parametrize("deployment,reasoning", [("gpt-4.1-mini", False), ("gpt-6-luna", True)])
def test_live_replay_references_pinned_agent_versions(monkeypatch, deployment, reasoning):
    from contextlib import nullcontext
    from types import SimpleNamespace
    from unittest.mock import Mock

    from cybersoc import foundry_demo

    settings = foundry_demo.FoundrySettings("https://demo.services.ai.azure.com/api/projects/demo", "3", "4", deployment, 61)
    project = Mock()
    project.agents.get_version.return_value = SimpleNamespace(
        definition=SimpleNamespace(model=deployment, tools=[])
    )
    sdk = Mock()
    project.get_openai_client.return_value = nullcontext(sdk)
    monkeypatch.setattr(foundry_demo, "project_client", lambda _endpoint: nullcontext(project))

    def respond(**request):
        payload = json.loads(request["input"])
        ids = [payload["evidence"][0]["evidence_id"]]
        if "triage" not in payload:
            result = {"severity": "high", "reason": "Synthetic correlation.", "evidence_ids": ids}
        else:
            result = {"summary": "Review case.", "limitations": ["Synthetic only."],
                      "next_step": "Verify with an analyst.", "evidence_ids": ids}
        return SimpleNamespace(status="completed", output_text=json.dumps(result))

    pauses = []
    monkeypatch.setattr(foundry_demo, "sleep", pauses.append)
    responses = sdk.with_options.return_value.responses
    responses.create.side_effect = respond
    output = foundry_demo.run_live_case(settings, "privileged-sign-in")
    refs = [call.kwargs["extra_body"]["agent_reference"] for call in responses.create.call_args_list]
    assert [(ref["name"], ref["version"]) for ref in refs] == [(TRIAGE_AGENT, "3"), (INVESTIGATION_AGENT, "4")]
    assert output["deployment"] == deployment
    assert pauses == [61]
    assert all(("reasoning" in call.kwargs) is reasoning for call in responses.create.call_args_list)
