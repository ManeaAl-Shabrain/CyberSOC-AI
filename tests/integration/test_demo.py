from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from apps.api.main import create_app


def test_dashboard_and_end_to_end_api():
    with TestClient(create_app(), base_url="http://localhost") as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
        assert 'id="scenario"' in response.text
        assert client.get("/assets/dashboard.js").status_code == 200
        assert client.get("/demo/runs/unknown").status_code == 404
        ids = [item["id"] for item in client.get("/demo/scenarios").json()]
        first = client.get(f"/demo/runs/{ids[0]}").json()
        second = client.get(f"/demo/runs/{ids[0]}").json()
        assert first["report"] == second["report"]
        assert first["trace_id"] != second["trace_id"]
        assert client.get("/demo/evaluation").json()["passed"] is True

        def replay(scenario_id):
            return client.get(f"/demo/runs/{scenario_id}")

        with ThreadPoolExecutor(max_workers=8) as pool:
            responses = list(pool.map(replay, ids * 8))
        assert all(result.status_code == 200 and result.json()["status"] == "reported" for result in responses)
        assert len({result.json()["trace_id"] for result in responses}) == 64


def test_reviewer_session():
    with TestClient(create_app(analyst_token="test-analyst", reviewer_token="test-reviewer"), base_url="http://localhost") as client:
        response = client.get("/approvals/session", headers={"Authorization": "Bearer test-reviewer"})
        assert response.json() == {"role": "demo-reviewer"}
