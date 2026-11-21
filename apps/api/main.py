from fastapi import FastAPI, HTTPException
from cybersoc.schemas.events import SecurityEvent
from cybersoc.repositories.events import EventRepository

app = FastAPI(title="CyberSOC AI", version="0.1.0")
repo = EventRepository()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/ready")
def ready():
    try:
        repo.connection.execute("SELECT 1").fetchone()
        return {"status": "ready", "mode": "local"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="storage unavailable") from exc

@app.post("/events", status_code=201)
def ingest(event: SecurityEvent):
    try:
        digest = repo.save(event)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"event_id": event.event_id, "sha256": digest}

@app.get("/events/{event_id}")
def get_event(event_id: str):
    result = repo.get(event_id)
    if not result:
        raise HTTPException(status_code=404, detail="not found")
    return result
