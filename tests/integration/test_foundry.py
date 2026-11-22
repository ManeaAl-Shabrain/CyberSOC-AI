from fastapi.testclient import TestClient

from apps.api import foundry
from apps.api.main import create_app
from cybersoc.foundry_demo import FoundrySettings

PROJECT = "https://synthetic.services.ai.azure.com/api/projects/demo"
HEADER = {"X-CyberSOC-Demo": "synthetic-only"}
REPLAY = "/demo/foundry/runs/"


def test_foundry_requires_configuration_and_intent_header():
    with TestClient(create_app(), base_url="http://localhost") as client:
        assert client.get("/demo/foundry/status").json() == {"configured": False, "deployment": None, "stage_delay_seconds": 0}
        assert client.post(REPLAY + "privileged-sign-in").status_code == 403
        assert client.post(REPLAY + "privileged-sign-in", headers=HEADER).status_code == 503


def test_foundry_endpoint_accepts_fixtures_and_redacts_provider_failure(monkeypatch):
    settings = FoundrySettings(PROJECT, "3", "4")
    scenarios = []

    def run_live_case(_settings, scenario):
        scenarios.append(scenario)
        if len(scenarios) == 1:
            raise RuntimeError("Sensitive upstream diagnostic")
        return {"scenario": scenario, "deployment": "gpt-4.1-mini", "human_review_required": True}

    monkeypatch.setattr(foundry, "run_live_case", run_live_case)
    with TestClient(create_app(foundry=settings), base_url="http://localhost") as client:
        assert client.get("/demo/foundry/status").json() == {"configured": True, "deployment": "gpt-4.1-mini", "stage_delay_seconds": 0}
        assert client.post(REPLAY + "unknown", headers=HEADER).status_code == 404
        failure = client.post(REPLAY + "privileged-sign-in", headers=HEADER)
        assert failure.status_code == 502
        assert "Sensitive upstream" not in failure.text
        response = client.post(REPLAY + "privileged-sign-in", headers=HEADER)
        assert response.status_code == 200
        assert response.json()["human_review_required"] is True

    assert scenarios == ["privileged-sign-in", "privileged-sign-in"]


def test_foundry_rejects_overlapping_replays(monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    settings = FoundrySettings(PROJECT, "3", "4")
    running = Event()
    finish = Event()

    def run_live_case(_settings, scenario):
        running.set()
        assert finish.wait(timeout=5)
        return {"scenario": scenario}

    monkeypatch.setattr(foundry, "run_live_case", run_live_case)
    with TestClient(create_app(foundry=settings), base_url="http://localhost") as client, ThreadPoolExecutor() as pool:
        first = pool.submit(client.post, REPLAY + "privileged-sign-in", headers=HEADER)
        try:
            assert running.wait(timeout=5)
            assert client.post(REPLAY + "routine-sign-in", headers=HEADER).status_code == 429
        finally:
            finish.set()
        assert first.result(timeout=5).status_code == 200
