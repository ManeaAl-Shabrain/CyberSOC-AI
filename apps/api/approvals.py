from enum import StrEnum
from hmac import compare_digest
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from cybersoc.orchestration.workflow import run_case
from cybersoc.scenarios import synthetic_case
from cybersoc.schemas.events import Severity
from cybersoc.services.approvals import ActionStatus


class Role(StrEnum):
    analyst = "demo-analyst"
    reviewer = "demo-reviewer"


class Command(StrEnum):
    approve = "approve"
    deny = "deny"
    simulate = "simulate"


COMMANDS = {Command.approve: ActionStatus.approved, Command.deny: ActionStatus.rejected,
            Command.simulate: ActionStatus.simulated_execution}


def create_approval_router(analyst_token: str | None, reviewer_token: str | None) -> APIRouter:
    configured = bool(analyst_token and reviewer_token and analyst_token != reviewer_token)
    router = APIRouter(prefix="/approvals")

    def role(authorization: Annotated[str | None, Header()] = None) -> Role:
        if not configured:
            raise HTTPException(503, "configure distinct demo analyst and reviewer tokens")
        presented = (authorization or "").encode()
        if compare_digest(presented, f"Bearer {analyst_token}".encode()):
            return Role.analyst
        if compare_digest(presented, f"Bearer {reviewer_token}".encode()):
            return Role.reviewer
        raise HTTPException(401, "authentication required", headers={"WWW-Authenticate": "Bearer"})

    def reviewer(identity: Annotated[Role, Depends(role)]) -> Role:
        if identity != Role.reviewer:
            raise HTTPException(403, "reviewer role required")
        return identity

    @router.get("")
    def list_approvals(request: Request, identity: Annotated[Role, Depends(role)]):
        return request.app.state.approvals.list_records(identity if identity == Role.analyst else None)

    @router.get("/audit")
    def list_audit(request: Request, _: Annotated[Role, Depends(reviewer)]):
        return request.app.state.approvals.audit()

    @router.post("/request/{scenario_id}", status_code=201)
    def request_approval(scenario_id: str, request: Request, identity: Annotated[Role, Depends(role)]):
        if identity != Role.analyst:
            raise HTTPException(403, "analyst role required")
        scenario = synthetic_case(scenario_id)
        if scenario is None:
            raise HTTPException(404, "unknown synthetic scenario")
        result = run_case(scenario)
        if result.report is None or result.report.severity not in {Severity.high, Severity.critical}:
            raise HTTPException(409, "case does not qualify for a simulation request")
        return request.app.state.approvals.request(result.case_id, identity)

    @router.post("/{action_id}/{command}")
    def transition(action_id: str, command: Command, request: Request, identity: Annotated[Role, Depends(reviewer)]):
        try:
            return request.app.state.approvals.transition(action_id, COMMANDS[command], identity)
        except KeyError as exc:
            raise HTTPException(404, "approval request not found") from exc
        except PermissionError as exc:
            raise HTTPException(409, str(exc)) from exc

    return router
