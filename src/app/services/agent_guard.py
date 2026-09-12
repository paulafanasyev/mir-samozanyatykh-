"""Safety and outbound data-loss prevention gateway for Svetlana.

The model is never trusted with authorization. This module also protects the
boundary to external AI providers: secrets are removed, direct identifiers are
redacted, and high-risk financial/identity material is blocked from external
providers by default.
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
    r"Bearer\s+[A-Za-z0-9._~+/=-]{20,}",
)
PII_PATTERNS = (
    r"\b[A-ZА-ЯЁ0-9._%+-]+@[A-ZА-ЯЁ0-9.-]+\.[A-ZА-ЯЁ]{2,}\b",
    r"(?<!\d)(?:\+?7|8)[\s().-]?\d{3}[\s().-]?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}(?!\d)",
    r"(?<!\d)\d{10,12}(?!\d)",
    r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)",
    r"\b(?:паспорт|passport)\s*(?:серия)?\s*[№#]?\s*[A-ZА-ЯЁ0-9 -]{4,20}\b",
)
HIGH_RISK_PATTERNS = (
    r"\b(?:банковск(?:ие|их)|bank|карта|card|сч[её]т|account|CVV|CVC|PIN|пароль|password|паспорт|passport|ключ|private key|seed phrase|секрет)\b",
    r"\b(?:ИНН|СНИЛС|ОГРН|КПП)\b",
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

@dataclass(frozen=True)
class ExternalDataResult:
    allowed: bool
    risk: str
    reasons: tuple[str, ...]
    sanitized_text: str


def _matches(patterns: tuple[str, ...], text: str) -> bool:
    return any(re.search(p, text, flags=re.IGNORECASE | re.DOTALL) for p in patterns)


def sanitize(message: str) -> str:
    text = " ".join(str(message or "").split())
    for pattern in SECRET_PATTERNS:
        text = re.sub(pattern, "[СЕКРЕТ УДАЛЁН]", text, flags=re.IGNORECASE)
    for pattern in PII_PATTERNS:
        text = re.sub(pattern, "[ПЕРСОНАЛЬНЫЕ ДАННЫЕ УДАЛЕНЫ]", text, flags=re.IGNORECASE)
    return text[:8000]


def prepare_external(message: str, context: str | None = None) -> ExternalDataResult:
    """Prepare content for an external model.

    Policy: secrets are always removed; direct identifiers are redacted;
    high-risk identity/financial material is not sent to an external provider.
    This is a technical DLP control and does not claim that any provider trains
    on the submitted data. Provider-specific retention/training terms remain a
    separate policy decision.
    """
    combined = " ".join(part for part in (message, context) if part)
    reasons: list[str] = []
    if _matches(HIGH_RISK_PATTERNS, combined):
        reasons.append("внешней модели запрещено передавать высокорисковые финансовые/идентификационные данные")
        return ExternalDataResult(False, "high", tuple(reasons), "")
    sanitized = sanitize(combined)
    if "[СЕКРЕТ УДАЛЁН]" in sanitized:
        reasons.append("секреты удалены до передачи внешней модели")
    if "[ПЕРСОНАЛЬНЫЕ ДАННЫЕ УДАЛЕНЫ]" in sanitized:
        reasons.append("прямые персональные идентификаторы удалены до передачи внешней модели")
    return ExternalDataResult(True, "medium" if reasons else "low", tuple(reasons), sanitized[:12000])


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
