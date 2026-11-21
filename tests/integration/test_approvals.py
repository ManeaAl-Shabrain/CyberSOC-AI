import pytest
from fastapi.testclient import TestClient

from apps.api.main import create_app

ANALYST = {"Authorization": "Bearer test-analyst"}
REVIEWER = {"Authorization": "Bearer test-reviewer"}
PATH = "/approvals/request/privileged-sign-in"


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(str(tmp_path / "demo.db"), analyst_token="test-analyst", reviewer_token="test-reviewer"),
                    base_url="http://localhost") as active:
        yield active


def test_auth_and_eligibility(client):
    assert client.post(PATH).status_code == 401
    assert client.post(PATH, headers=REVIEWER).status_code == 403
    assert client.post("/approvals/request/unknown", headers=ANALYST).status_code == 404
    assert client.post("/approvals/request/routine-sign-in", headers=ANALYST).status_code == 409
    assert client.get("/approvals/audit", headers=ANALYST).status_code == 403
    assert client.post("/approvals/missing/deny", headers=REVIEWER).status_code == 404


@pytest.mark.parametrize("configured", [{}, {"analyst_token": "same", "reviewer_token": "same"}])
def test_disabled_without_distinct_tokens(configured):
    with TestClient(create_app(**configured), base_url="http://localhost") as client:
        assert client.post(PATH).status_code == 503


def test_approve_and_record_simulation(client):
    record = client.post(PATH, headers=ANALYST).json()
    action = f"/approvals/{record['id']}"
    assert client.post(PATH, headers=ANALYST).json() == record
    assert client.post(f"{action}/approve", headers=ANALYST).status_code == 403
    assert client.post(f"{action}/simulate", headers=REVIEWER).status_code == 409
    assert client.post(f"{action}/approve", headers=REVIEWER).json()["approved_by"] == "demo-reviewer"
    assert client.post(f"{action}/simulate", headers=REVIEWER).json()["status"] == "simulated_execution"
    assert client.post(f"{action}/simulate", headers=REVIEWER).status_code == 409
    assert len(client.get("/approvals", headers=ANALYST).json()) == 1
    assert len(client.get("/approvals", headers=REVIEWER).json()) == 1
    audit = client.get("/approvals/audit", headers=REVIEWER).json()
    assert [entry["status"] for entry in audit] == ["awaiting_approval", "approved", "simulated_execution"]
    assert [entry["actor"] for entry in audit] == ["demo-analyst", "demo-reviewer", "demo-reviewer"]


def test_denial_is_terminal(client):
    action_id = client.post(PATH, headers=ANALYST).json()["id"]
    action = f"/approvals/{action_id}"
    assert client.post(f"{action}/deny", headers=REVIEWER).json()["status"] == "rejected"
    assert client.post(f"{action}/approve", headers=REVIEWER).status_code == 409
    assert client.post(f"{action}/simulate", headers=REVIEWER).status_code == 409
