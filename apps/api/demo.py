from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from cybersoc.evaluation import evaluate
from cybersoc.orchestration.workflow import run_case
from cybersoc.scenarios import dataset, synthetic_case

WEB_PATH = Path(__file__).with_name("web")
router = APIRouter()


@router.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(
        WEB_PATH / "index.html",
        headers={
            "Content-Security-Policy": "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; "
            "img-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer",
            "Cache-Control": "no-store",
        },
    )


@router.get("/demo/scenarios")
def scenarios():
    return [{"id": item.id, "title": item.title} for item in dataset().scenarios]


@router.get("/demo/runs/{scenario_id}")
def replay(scenario_id: str):
    scenario = synthetic_case(scenario_id)
    if scenario is None:
        raise HTTPException(404, "unknown synthetic scenario")
    return run_case(scenario)


@router.get("/demo/evaluation")
def evaluation():
    return evaluate()


static = StaticFiles(directory=WEB_PATH)
