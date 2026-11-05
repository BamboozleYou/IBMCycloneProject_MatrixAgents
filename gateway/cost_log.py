"""SQLite cost log — one row per LLM call."""
import sqlite3, json
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "costs.db"


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as con:
        con.execute(
            """CREATE TABLE IF NOT EXISTS costs (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                ts           TEXT NOT NULL,
                agent        TEXT NOT NULL,
                model        TEXT NOT NULL,
                tokens_in    INTEGER NOT NULL DEFAULT 0,
                tokens_out   INTEGER NOT NULL DEFAULT 0,
                usd_estimate REAL NOT NULL DEFAULT 0.0
            )"""
        )


def log_call(agent: str, model: str, usage: dict) -> None:
    """usage dict may contain prompt_tokens, completion_tokens, total_tokens."""
    init_db()
    tokens_in  = usage.get("prompt_tokens",     usage.get("input_tokens",  0))
    tokens_out = usage.get("completion_tokens",  usage.get("output_tokens", 0))
    # rough estimate: $0.50 / 1M input, $1.50 / 1M output
    usd = (tokens_in * 0.5 + tokens_out * 1.5) / 1_000_000
    ts = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(DB_PATH) as con:
        con.execute(
            "INSERT INTO costs (ts, agent, model, tokens_in, tokens_out, usd_estimate) VALUES (?,?,?,?,?,?)",
            (ts, agent, model, tokens_in, tokens_out, usd),
        )
