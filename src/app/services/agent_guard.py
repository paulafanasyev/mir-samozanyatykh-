"""Safety gateway for Svetlana's future agentic capabilities.

The model is never trusted with authorization. This module classifies input,
strips common prompt-injection framing, and requires explicit confirmation for
side-effecting actions. It deliberately does not execute tools.
"""
from __future__ import annotations
import re
from dataclasses import dataclass

INJECTION_PATTERNS = (
    r"ignore\s+(all|any|previous|prior)\s+instructions",
    r"(system|developer)\s+prompt",
    r"reveal\s+(your|the)\s+(hidden|system|developer)",
    r"show\s+(me\s+)?(your|the)\s+instructions",
    r"bypass\s+(security|safety|authorization)",
    r"pretend\s+you\s+are\s+(the\s+)?admin",
    r"disable\s+(security|logging|audit)",
)
SECRET_PATTERNS = (
    r"sk-[A-Za-z0-9_-]{16,}",
    r"AIza[0-9A-Za-z_-]{20,}",
    r"gh[pousr]_[A-Za-z0-9_]{20,}",
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
)
SIDE_EFFECT_PATTERNS = (
    r"(удали|удалить|delete|destroy|переведи|transfer|оплати|pay)",
    r"(отправь|send)\s+(письмо|email|сообщение|message)",
    r"(измени|изменить|change|update)\s+(пароль|роль|права|permission)",
    r"(создай|создать|create)\s+(платёж|payment|пользователя|user)",
)

@dataclass(frozen=True)
class GuardResult:
    allowed: bool
    risk: str
    reasons: tuple[str, ...]
    sanitized_message: str
    requires_confirmation: bool


def _matches(patterns: tuple[str, ...], text: str) -> bool:
    return any(re.search(p, text, flags=re.IGNORECASE | re.DOTALL) for p in patterns)


def sanitize(message: str) -> str:
    text = " ".join(str(message or "").split())
    for pattern in SECRET_PATTERNS:
        text = re.sub(pattern, "[СЕКРЕТ УДАЛЁН]", text, flags=re.IGNORECASE)
    return text[:8000]


def inspect(message: str) -> GuardResult:
    clean = sanitize(message)
    reasons: list[str] = []
    if _matches(INJECTION_PATTERNS, clean):
        reasons.append("обнаружена попытка подмены инструкций или обхода защиты")
    if "[СЕКРЕТ УДАЛЁН]" in clean:
        reasons.append("обнаружен похожий на секрет фрагмент")
    side_effect = _matches(SIDE_EFFECT_PATTERNS, clean)
    if side_effect:
        reasons.append("запрос может привести к изменению внешнего состояния")
    if any("обнаружена попытка" in x for x in reasons):
        return GuardResult(False, "high", tuple(reasons), clean, False)
    if side_effect:
        return GuardResult(True, "medium", tuple(reasons), clean, True)
    return GuardResult(True, "low", tuple(reasons), clean, False)
