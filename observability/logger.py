"""Structured JSON logger using structlog."""
from __future__ import annotations
import logging
import sys
from pathlib import Path

import structlog

_LOG_DIR = Path(__file__).parent.parent / "logs"
_LOG_DIR.mkdir(exist_ok=True)
_LOG_FILE = _LOG_DIR / "app.log"

# File handler
_file_handler = logging.FileHandler(_LOG_FILE)
_file_handler.setLevel(logging.DEBUG)

logging.basicConfig(
    level=logging.DEBUG,
    handlers=[logging.StreamHandler(sys.stdout), _file_handler],
    format="%(message)s",
)

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

_logger = structlog.get_logger("cycloneshield")


def log_call(
    agent: str,
    model: str,
    duration_ms: float,
    status: str,
    tokens: int = 0,
) -> None:
    _logger.info(
        "llm_call",
        agent=agent,
        model=model,
        duration_ms=round(duration_ms, 2),
        status=status,
        tokens=tokens,
    )
