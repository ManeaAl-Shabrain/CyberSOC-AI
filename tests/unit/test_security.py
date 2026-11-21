import pytest
from pydantic import ValidationError

from cybersoc.providers.base import FoundryProvider, MockProvider
from cybersoc.repositories.events import EventRepository
from cybersoc.schemas.events import AgentFinding, SecurityEvent
from cybersoc.services.approvals import ActionStatus, ProposedAction


@pytest.mark.parametrize("status", [ActionStatus.approved, ActionStatus.rejected, ActionStatus.simulated_execution])
def test_no_direct_privileged_transition(status):
    with pytest.raises(PermissionError):
        ProposedAction("A1").transition(status, "agent")

def test_unauthorized_approval_denied():
    a = ProposedAction("A1").transition(ActionStatus.awaiting_approval, "agent")
    with pytest.raises(PermissionError):
        a.transition(ActionStatus.approved, "agent")

def test_approved_simulation():
    a = ProposedAction("A1").transition(ActionStatus.awaiting_approval, "agent")
    a = a.transition(ActionStatus.approved, "analyst", authorized_approver=True)
    assert a.transition(ActionStatus.simulated_execution, "runner").status == ActionStatus.simulated_execution

def test_no_evidence_requires_unverified():
    with pytest.raises(ValidationError):
        AgentFinding(agent_id="x", statement="safe", confidence=.8)
    assert AgentFinding(agent_id="x", statement="unknown", confidence=.2, unverified=True).unverified

def test_duplicate_evidence_denied():
    with pytest.raises(ValidationError):
        AgentFinding(agent_id="x", statement="x", confidence=.5, evidence_ids=["1", "1"])

def test_mock_is_offline():
    assert MockProvider().analyze({})["provider"] == "mock"

def test_foundry_fail_closed():
    with pytest.raises(RuntimeError):
        FoundryProvider().analyze({})

def test_storage_immutable():
    event = SecurityEvent(event_id="1", timestamp="2026-11-20T10:30:00Z", source="x", event_type="y", asset_id="z")
    with EventRepository() as repository:
        digest = repository.save(event)
        assert repository.get("1")["sha256"] == digest
        with pytest.raises(ValueError):
            repository.save(event)
