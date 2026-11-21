from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)
EVENT = {"event_id":"EV-INTEGRATION-1","timestamp":"2026-11-20T10:30:00Z","source":"Sysmon","event_type":"process_creation","asset_id":"WIN11-01","raw_data":{"process":"powershell.exe"}}

def test_health():
    assert client.get("/health").json() == {"status": "ok"}

def test_ready():
    assert client.get("/ready").status_code == 200

def test_ingest_and_read():
    response = client.post("/events", json=EVENT)
    assert response.status_code == 201
    assert len(response.json()["sha256"]) == 64
    assert client.get("/events/EV-INTEGRATION-1").json()["event"]["source"] == "Sysmon"

def test_duplicate_rejected():
    assert client.post("/events", json=EVENT).status_code == 409

def test_bad_event_rejected():
    bad = {**EVENT, "event_id": "EV-BAD", "timestamp": "2026-11-20T10:30:00"}
    assert client.post("/events", json=bad).status_code == 422

def test_missing_event():
    assert client.get("/events/no-such-event").status_code == 404
