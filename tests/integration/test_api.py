import pytest
from fastapi.testclient import TestClient

from apps.api.main import create_app

EVENT = {
    "event_id": "EV-INTEGRATION-1",
    "timestamp": "2026-11-20T10:30:00Z",
    "source": "Sysmon",
    "event_type": "process_creation",
    "asset_id": "WIN11-01",
    "raw_data": {"process": "synthetic-process.exe"},
}


@pytest.fixture
def client():
    with TestClient(create_app(), base_url="http://localhost") as active:
        yield active


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_ready(client):
    assert client.get("/ready").status_code == 200


def test_ingest_and_read(client):
    response = client.post("/events", json=EVENT)
    assert response.status_code == 201
    assert len(response.json()["sha256"]) == 64
    assert client.get("/events/EV-INTEGRATION-1").json()["event"]["source"] == "Sysmon"


def test_duplicate_rejected(client):
    assert client.post("/events", json=EVENT).status_code == 201
    assert client.post("/events", json=EVENT).status_code == 409


@pytest.mark.parametrize("changes", [
    {"timestamp": "2026-11-20T10:30:00"},
    {"simulation": False},
    {"unexpected": "input"},
    {"raw_data": {"message": "x" * 13_000}},
])
def test_bad_event_rejected(client, changes):
    response = client.post("/events", json={**EVENT, **changes})
    assert response.status_code == 422
    assert response.json() == {"detail": "invalid synthetic event"}


def test_missing_event(client):
    assert client.get("/events/no-such-event").status_code == 404


def test_body_limit_and_media_type(client):
    assert client.post("/events", json={**EVENT, "raw_data": {"message": "x" * 17_000}}).status_code == 413
    assert client.post("/events", content="{}").status_code == 415


def test_host_and_token_restrictions():
    with TestClient(create_app(api_token="synthetic-test-token"), base_url="http://localhost") as client:
        assert client.post("/events", json=EVENT).status_code == 401
        assert client.get("/events/unknown", headers={"Authorization": "Bearer invalid"}).status_code == 401
        assert client.get("/health", headers={"Host": "external.example"}).status_code == 400
        assert client.post("/events", json=EVENT, headers={"Authorization": "Bearer synthetic-test-token"}).status_code == 201
