"""Opt-in endpoint for the synthetic Foundry replay."""

import logging
from threading import Lock

from fastapi import APIRouter, HTTPException, Request

from cybersoc.foundry_demo import FoundrySettings, run_live_case
from cybersoc.scenarios import synthetic_case

logger = logging.getLogger(__name__)


def create_foundry_router(settings: FoundrySettings | None) -> APIRouter:
    router = APIRouter(prefix="/demo/foundry")
    active_run = Lock()

    @router.get("/status")
    def status():
        return {"configured": settings is not None, "deployment": settings.deployment if settings else None,
                "stage_delay_seconds": settings.stage_delay_seconds if settings else 0}

    @router.post("/runs/{scenario_id}")
    def replay(scenario_id: str, request: Request):
        if request.headers.get("x-cybersoc-demo") != "synthetic-only":
            raise HTTPException(403, "missing demo request header")
        if settings is None:
            raise HTTPException(503, "Foundry replay is not configured")
        if synthetic_case(scenario_id) is None:
            raise HTTPException(404, "unknown synthetic scenario")
        if not active_run.acquire(blocking=False):
            raise HTTPException(429, "a Foundry replay is already running")
        try:
            return run_live_case(settings, scenario_id)
        except Exception as exc:  # noqa: BLE001 -- redact provider and contract failures
            logger.warning("Foundry synthetic replay failed (%s)", type(exc).__name__)
            raise HTTPException(502, "Foundry replay failed. Check the deployment, quota, and pinned agent versions.") from None
        finally:
            active_run.release()

    return router
