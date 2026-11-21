from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from hmac import compare_digest
from os import getenv
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool
from starlette.middleware.trustedhost import TrustedHostMiddleware

from cybersoc.repositories.events import DuplicateEvent, EventRepository
from cybersoc.schemas.events import SecurityEvent

MAX_EVENT_BYTES = 16_384


def create_app(database: str = ":memory:", api_token: str | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        with EventRepository(database) as repository:
            application.state.events = repository
            yield

    app = FastAPI(title="CyberSOC AI", version="0.1.0", lifespan=lifespan)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "[::1]"])

    def require_token(authorization: Annotated[str | None, Header()] = None) -> None:
        if api_token and not compare_digest((authorization or "").encode(), f"Bearer {api_token}".encode()):
            raise HTTPException(401, "authentication required", headers={"WWW-Authenticate": "Bearer"})

    protected = [Depends(require_token)]

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/ready")
    def ready(request: Request):
        if not request.app.state.events.ready():
            raise HTTPException(503, "storage unavailable")
        return {"status": "ready", "mode": "local"}

    @app.post("/events", status_code=201, dependencies=protected)
    async def ingest(request: Request):
        if request.headers.get("content-type", "").partition(";")[0].lower().strip() != "application/json":
            raise HTTPException(415, "expected application/json")
        body = bytearray()
        async for chunk in request.stream():
            if len(body) + len(chunk) > MAX_EVENT_BYTES:
                raise HTTPException(413, "event exceeds size limit")
            body.extend(chunk)
        try:
            event = SecurityEvent.model_validate_json(body)
        except (ValidationError, RecursionError) as exc:
            raise HTTPException(422, "invalid synthetic event") from exc
        try:
            digest = await run_in_threadpool(request.app.state.events.save, event)
        except DuplicateEvent as exc:
            raise HTTPException(409, "duplicate event_id") from exc
        return {"event_id": event.event_id, "sha256": digest}

    @app.get("/events/{event_id}", dependencies=protected)
    def get_event(event_id: str, request: Request):
        result = request.app.state.events.get(event_id)
        if result is None:
            raise HTTPException(404, "not found")
        return result

    return app


app = create_app(database=getenv("CYBERSOC_DB", ":memory:"), api_token=getenv("CYBERSOC_API_TOKEN"))
