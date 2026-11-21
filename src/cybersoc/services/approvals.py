from dataclasses import dataclass
from enum import Enum


class ActionStatus(str, Enum):
    proposed = "proposed"
    awaiting_approval = "awaiting_approval"
    approved = "approved"
    rejected = "rejected"
    simulated_execution = "simulated_execution"

ALLOWED = {
    ActionStatus.proposed: {ActionStatus.awaiting_approval},
    ActionStatus.awaiting_approval: {ActionStatus.approved, ActionStatus.rejected},
    ActionStatus.approved: {ActionStatus.simulated_execution},
    ActionStatus.rejected: set(),
    ActionStatus.simulated_execution: set(),
}

@dataclass(frozen=True)
class ProposedAction:
    action_id: str
    status: ActionStatus = ActionStatus.proposed
    approved_by: str | None = None

    def transition(self, target: ActionStatus, actor: str, authorized_approver: bool = False):
        if target not in ALLOWED[self.status]:
            raise PermissionError("invalid state transition")
        if target in (ActionStatus.approved, ActionStatus.rejected) and not authorized_approver:
            raise PermissionError("authorized human approval required")
        if target == ActionStatus.simulated_execution and not self.approved_by:
            raise PermissionError("missing approval")
        from dataclasses import replace
        return replace(self, status=target, approved_by=actor if target == ActionStatus.approved else self.approved_by)
