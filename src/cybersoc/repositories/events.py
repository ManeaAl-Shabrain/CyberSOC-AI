import hashlib
import json
import sqlite3
from cybersoc.schemas.events import SecurityEvent

class EventRepository:
    def __init__(self, database: str = ":memory:"):
        self.connection = sqlite3.connect(database, check_same_thread=False)
        self.connection.execute("CREATE TABLE IF NOT EXISTS events (event_id TEXT PRIMARY KEY, payload TEXT NOT NULL, sha256 TEXT NOT NULL)")
        self.connection.commit()

    def save(self, event: SecurityEvent) -> str:
        payload = json.dumps(event.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(payload.encode()).hexdigest()
        try:
            with self.connection:
                self.connection.execute("INSERT INTO events VALUES (?, ?, ?)", (event.event_id, payload, digest))
        except sqlite3.IntegrityError as exc:
            raise ValueError("duplicate event_id") from exc
        return digest

    def get(self, event_id: str) -> dict | None:
        row = self.connection.execute("SELECT payload, sha256 FROM events WHERE event_id=?", (event_id,)).fetchone()
        return {"event": json.loads(row[0]), "sha256": row[1]} if row else None
