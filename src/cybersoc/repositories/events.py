import hashlib
import json
import sqlite3
from threading import Lock

from cybersoc.schemas.events import SecurityEvent


class DuplicateEvent(ValueError):
    pass


def event_digest(event: SecurityEvent) -> tuple[str, str]:
    payload = json.dumps(event.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), allow_nan=False)
    return payload, hashlib.sha256(payload.encode()).hexdigest()


class EventRepository:
    def __init__(self, database: str = ":memory:"):
        self._lock = Lock()
        self._connection = sqlite3.connect(database, check_same_thread=False)
        self._connection.execute("CREATE TABLE IF NOT EXISTS events (event_id TEXT PRIMARY KEY, payload TEXT NOT NULL, sha256 TEXT NOT NULL)")
        self._connection.commit()

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        with self._lock:
            self._connection.close()

    def ready(self) -> bool:
        try:
            with self._lock:
                self._connection.execute("SELECT 1 FROM events LIMIT 1").fetchone()
        except sqlite3.Error:
            return False
        return True

    def save(self, event: SecurityEvent) -> str:
        payload, digest = event_digest(event)
        try:
            with self._lock, self._connection:
                self._connection.execute("INSERT INTO events VALUES (?, ?, ?)", (event.event_id, payload, digest))
        except sqlite3.IntegrityError as exc:
            raise DuplicateEvent("duplicate event_id") from exc
        return digest

    def get(self, event_id: str) -> dict | None:
        with self._lock:
            row = self._connection.execute("SELECT payload, sha256 FROM events WHERE event_id=?", (event_id,)).fetchone()
        return {"event": json.loads(row[0]), "sha256": row[1]} if row else None
