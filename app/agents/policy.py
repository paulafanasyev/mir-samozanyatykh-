"""Safety and evidence policy for the agent loop.

This layer deliberately does not attempt to bypass provider safeguards. It
ensures that the project can route legitimate work while preserving explicit
safety, authorization, and verification boundaries.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str


FORBIDDEN_INSTRUCTION_MARKERS = (
    "disable safety",
    "bypass safety",
    "ignore provider policy",
    "jailbreak",
    "unrestricted mode",
    "remove safeguards",
)


def inspect_instruction(text: str) -> PolicyDecision:
    normalized = " ".join(text.lower().split())
    for marker in FORBIDDEN_INSTRUCTION_MARKERS:
        if marker in normalized:
            return PolicyDecision(False, f"instruction-policy marker detected: {marker}")
    return PolicyDecision(True, "no project-level bypass marker detected")


def require_evidence(evidence: Iterable[str]) -> PolicyDecision:
    items = [item for item in evidence if str(item).strip()]
    if not items:
        return PolicyDecision(False, "no evidence supplied")
    return PolicyDecision(True, "evidence present")
