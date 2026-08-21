"""Offline Svetlana runtime backed by the project's official-source knowledge base.

No network I/O is performed here. Legal/tax facts live in a versioned JSON file
with source URLs; the assistant never invents a legal answer when the local
knowledge base does not contain one.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

KNOWLEDGE_PATH = Path(__file__).resolve().parents[2] / "static" / "svetlana_knowledge_v4.json"


def _load_topics() -> list[dict[str, Any]]:
    try:
        data = json.loads(KNOWLEDGE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    topics = data.get("topics", {})
    if not isinstance(topics, dict):
        return []
    result: list[dict[str, Any]] = []
    for key, value in topics.items():
        if isinstance(value, dict):
            result.append({"id": key, **value})
    return result


def _tokens(text: str) -> set[str]:
    return {
        token.lower()
        for token in re.findall(r"[\wА-Яа-яЁё]+", text)
        if len(token) > 2
    }


def _rank_topics(message: str) -> list[tuple[int, dict[str, Any]]]:
    query = _tokens(message)
    if not query:
        return []
    ranked: list[tuple[int, dict[str, Any]]] = []
    for topic in _load_topics():
        keywords = " ".join(str(x) for x in topic.get("keywords", []))
        title = str(topic.get("title", ""))
        content = str(topic.get("content", ""))
        score = len(query & _tokens(keywords)) * 5
        score += len(query & _tokens(title)) * 3
        score += min(5, len(query & _tokens(content)))
        if score:
            ranked.append((score, topic))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return ranked


def _source_line(topic: dict[str, Any]) -> str:
    sources = [str(x) for x in topic.get("sources", []) if str(x).strip()]
    if not sources:
        return ""
    return "\n\nИсточник: " + "; ".join(sources)


def _workflow_answer(message: str) -> str | None:
    text = message.lower()
    if any(x in text for x in ("создай договор", "составь договор", "нужен договор", "сделай договор", "создай акт", "составь акт")):
        return (
            "Конечно. Я могу помочь собрать данные для договора или акта и передать их в модуль документов. "
            "Откройте раздел «Документы», выберите шаблон, заполните стороны, предмет, стоимость и сроки. "
            "Перед подписанием обязательно проверьте реквизиты и юридические условия.\n\n"
            "Документы: /contracts"
        )
    if any(x in text for x in ("добавь в календарь", "поставь в календарь", "в календарь", "напомни мне", "встречу")):
        return (
            "Помогу организовать рабочий план. Для встречи или дедлайна нужны дата, время, название и при необходимости клиент/проект. "
            "Рабочий раздел календаря: /calendar"
        )
    if any(x in text for x in ("добавь клиента", "новый клиент", "в crm", "карточку клиента", "сделку")):
        return (
            "Для ведения клиента используйте CRM: карточка клиента → контактные данные → сделка → статус → следующая задача. "
            "Рабочий раздел CRM: /crm"
        )
    if any(x in text for x in ("налог посчитай", "рассчитай налог", "калькулятор", "сколько налога")):
        return "Для ориентировочного расчёта НПД откройте калькулятор: /calculator. Ставка зависит от категории заказчика."
    return None


def answer_local(message: str, context: str | None = None) -> str:
    message = str(message or "").strip()
    if not message:
        return "Сформулируйте вопрос — я помогу с НПД, документами, клиентами, календарём, поддержкой или развитием проекта."

    workflow = _workflow_answer(message)
    if workflow:
        return workflow

    ranked = _rank_topics(message)
    if ranked:
        # Combine the two strongest local topics when the user asks a multi-part question.
        selected = [topic for score, topic in ranked[:2] if score >= 5]
        parts: list[str] = []
        for topic in selected:
            title = str(topic.get("title", "Ответ Светланы")).strip()
            content = str(topic.get("content", "")).strip()
            parts.append(f"{title}\n\n{content}{_source_line(topic)}")
        if parts:
            return "\n\n---\n\n".join(parts)

    text = message.lower()
    if any(word in text for word in ("привет", "здравств", "добрый", "доброе")):
        return (
            "Здравствуйте! Я Светлана — собственный офлайн-помощник «Мира Самозанятых». "
            "Я работаю на локальной базе знаний без обращения к внешнему AI. "
            "Могу помочь с НПД, документами, клиентами, календарём, CRM, поддержкой и развитием проекта."
        )

    if context:
        return (
            "В моей локальной базе сейчас нет достаточно надёжного ответа на этот вопрос. "
            "Я не буду придумывать нормативные сведения. Попробуйте уточнить вопрос про НПД, чеки, "
            "налоги, договоры, акты, клиентов, календарь, CRM или меры поддержки."
        )

    return (
        "Я Светлана, собственный локальный ИИ-помощник «Мира Самозанятых». "
        "Я не отправляю ваш вопрос во внешний AI. Если вопрос юридический или налоговый, "
        "я опираюсь только на загруженные официальные источники и указываю источник; "
        "если данных недостаточно — прямо скажу об этом."
    )


def local_status() -> dict[str, Any]:
    topics = _load_topics()
    return {
        "mode": "offline",
        "provider": "local",
        "network_required": False,
        "knowledge_base": KNOWLEDGE_PATH.name,
        "knowledge_topics": len(topics),
        "llm_runtime": "local_knowledge_runtime",
        "documents_repository": "genoffice",
        "message": "Светлана работает локально. Внешний AI-провайдер для этого endpoint не используется.",
    }
