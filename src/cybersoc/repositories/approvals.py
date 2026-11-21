import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from threading import Lock
from uuid import uuid4

from cybersoc.schemas.cases import Contract
from cybersoc.services.approvals import ActionStatus, ProposedAction


class ApprovalRecord(Contract):
    id: str
    case_id: str
    requester: str
    status: ActionStatus
    approved_by: str | None


class AuditRecord(Contract):
    action_id: str
    actor: str
    status: ActionStatus
    timestamp: datetime


class ApprovalRepository:
    def __init__(self, database: str):
        self._lock = Lock()
        self._connection = sqlite3.connect(database, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._connection.executescript("""
            CREATE TABLE IF NOT EXISTS approvals (
                id TEXT PRIMARY KEY, case_id TEXT NOT NULL, requester TEXT NOT NULL,
                status TEXT NOT NULL, approved_by TEXT,
                UNIQUE(case_id, requester)
            );
            CREATE TABLE IF NOT EXISTS approval_audit (
                sequence INTEGER PRIMARY KEY, action_id TEXT NOT NULL,
                actor TEXT NOT NULL, status TEXT NOT NULL, timestamp TEXT NOT NULL
            );
        """)

    def close(self):
        with self._lock:
            self._connection.close()

    def list_records(self, requester: str | None = None) -> list[ApprovalRecord]:
        with self._lock, closing(self._connection.cursor()) as cursor:
            rows = cursor.execute(
                "SELECT * FROM approvals WHERE (? IS NULL OR requester = ?) ORDER BY rowid", (requester, requester),
            ).fetchall()
        return [ApprovalRecord(**dict(row)) for row in rows]

    def audit(self) -> list[AuditRecord]:
        with self._lock, closing(self._connection.cursor()) as cursor:
            rows = cursor.execute("SELECT action_id, actor, status, timestamp FROM approval_audit ORDER BY sequence").fetchall()
        return [AuditRecord(**dict(row)) for row in rows]

    def request(self, case_id: str, actor: str) -> ApprovalRecord:
        with self._lock, self._connection, closing(self._connection.cursor()) as cursor:
            cursor.execute("BEGIN IMMEDIATE")
            row = cursor.execute("SELECT * FROM approvals WHERE case_id=? AND requester=?", (case_id, actor)).fetchone()
            if row:
                return ApprovalRecord(**dict(row))
            record = ApprovalRecord(id=uuid4().hex, case_id=case_id, requester=actor,
                                    status=ActionStatus.awaiting_approval, approved_by=None)
            cursor.execute("INSERT INTO approvals VALUES (?, ?, ?, ?, ?)",
                           (record.id, record.case_id, record.requester, record.status, record.approved_by))
            self._audit(cursor, record, actor)
            return record

    def transition(self, action_id: str, target: ActionStatus, actor: str) -> ApprovalRecord:
        with self._lock, self._connection, closing(self._connection.cursor()) as cursor:
            cursor.execute("BEGIN IMMEDIATE")
            row = cursor.execute("SELECT * FROM approvals WHERE id=?", (action_id,)).fetchone()
            if row is None:
                raise KeyError(action_id)
            record = ApprovalRecord(**dict(row))
            if record.requester == actor:
                raise PermissionError("requesters cannot review their own actions")
            action = ProposedAction(record.id, record.status, record.approved_by)
            changed = action.transition(target, actor, authorized_approver=True)
            updated = ApprovalRecord(id=record.id, case_id=record.case_id, requester=record.requester,
                                     status=changed.status, approved_by=changed.approved_by)
            cursor.execute("UPDATE approvals SET status=?, approved_by=? WHERE id=?",
                           (updated.status, updated.approved_by, updated.id))
            self._audit(cursor, updated, actor)
            return updated

    @staticmethod
    def _audit(cursor: sqlite3.Cursor, record: ApprovalRecord, actor: str) -> None:
        cursor.execute(
            "INSERT INTO approval_audit (action_id, actor, status, timestamp) VALUES (?, ?, ?, ?)",
            (record.id, actor, record.status, datetime.now(UTC).isoformat()),
        )
