"""SQLite audit log — tamper-evident record of every agent action."""
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "audit.db"


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as con:
        con.execute(
            """CREATE TABLE IF NOT EXISTS audit (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                ts           TEXT NOT NULL,
                agent        TEXT NOT NULL,
                action       TEXT NOT NULL,
                approved_by  TEXT,
                payload_hash TEXT NOT NULL
            )"""
        )


def log_action(agent: str, action: str, payload: dict, approved_by: str | None = None) -> None:
    init_db()
    payload_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode()
    ).hexdigest()
    ts = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(DB_PATH) as con:
        con.execute(
            "INSERT INTO audit (ts, agent, action, approved_by, payload_hash) VALUES (?,?,?,?,?)",
            (ts, agent, action, approved_by, payload_hash),
        )
