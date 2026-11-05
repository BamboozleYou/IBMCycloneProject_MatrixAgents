"""Regex guardrails — input injection detection and output PII check."""
import re

INJECTION_PATTERNS = [
    re.compile(r"ignore previous", re.IGNORECASE),
    re.compile(r"ignore all previous", re.IGNORECASE),
    re.compile(r"system\s*:", re.IGNORECASE),
    re.compile(r"<\|im_start\|>"),
    re.compile(r"<\|im_end\|>"),
    re.compile(r"<\|system\|>"),
    re.compile(r"you are now", re.IGNORECASE),
    re.compile(r"disregard (all|your|the) (previous|instructions|system)", re.IGNORECASE),
    re.compile(r"jailbreak", re.IGNORECASE),
]

PII_PATTERNS = [
    re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b"),          # Aadhaar-format
    re.compile(r"\b\d{10}\b"),                          # 10-digit phone
    re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),  # email
]


class GuardError(ValueError):
    """Raised when guardrail check fails."""


def check_input(text: str) -> None:
    """Raises GuardError if text contains prompt-injection patterns."""
    for pat in INJECTION_PATTERNS:
        if pat.search(text):
            raise GuardError(f"Input blocked by guardrail — matched pattern: {pat.pattern!r}")


def check_output(text: str) -> None:
    """Raises GuardError if output contains PII patterns."""
    for pat in PII_PATTERNS:
        if pat.search(text):
            raise GuardError(f"Output blocked by guardrail — PII pattern detected: {pat.pattern!r}")
