"""Offline Svetlana runtime backed by the versioned local knowledge base.

This module intentionally performs no network I/O. It is a working offline
assistant backed by the project's versioned Svetlana knowledge base. A real
embedded LLM can later be added behind the same function without introducing
cloud-provider dependencies into the API contract.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

KNOWLEDGE_PATH = Path(__file__).resolve().parents[2] / "static" / "svetlana_knowledge_v3.json"


def _load_topics() -> list[dict[str, Any]]:
    try:
        data = json.loads(KNOWLEDGE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    topics = data.get("topics", {})
    if not isinstance(topics, dict):
        return []
    result: list[dict[str, Any]] = []
    for value in topics.values():
        if isinstance(value, dict):
            result.append(value)
    return result


def _tokens(text: str) -> set[str]:
    return {token.lower() for token in re.findall(r"[\wА-Яа-яЁё]+", text) if len(token) > 2}


def _find_topic(message: str) -> dict[str, Any] | None:
    query = _tokens(message)
    if not query:
        return None
    best: tuple[int, dict[str, Any] | None] = (0, None)
    for topic in _load_topics():
        keywords = topic.get("keywords", [])
        haystack = " ".join(str(x) for x in keywords)
        score = len(query & _tokens(haystack))
        if score > best[0]:
            best = (score, topic)
    return best[1] if best[0] else None


def answer_local(message: str, context: str | None = None) -> str:
    topic = _find_topic(message)
    if topic:
        title = str(topic.get("title", "Ответ Светланы")).strip()
        content = str(topic.get("content", "")).strip()
        return f"{title}\n\n{content}"

    if any(word in message.lower() for word in ("привет", "здравств", "добрый", "доброе")):
        return (
            "Здравствуйте! Я Светлана. Я работаю локально, без облачного AI. "
            "Могу помочь по самозанятости, НПД, налогам, документам и работе на платформе."
        )

    if context:
        return (
            "Я работаю в офлайн-режиме и не отправляю ваш запрос во внешний AI. "
            "В текущей локальной базе нет точного ответа на этот вопрос. "
            "Сформулируйте его через НПД, налоги, документы, гранты, кредиты или работу самозанятого."
        )

    return (
        "Я Светлана, локальный помощник «Мира Самозанятых». "
        "Сейчас у меня доступна локальная база знаний по самозанятости, НПД, "
        "налогам, поддержке, документам и финансам. Уточните вопрос — я найду "
        "соответствующий раздел без обращения к внешнему AI."
    )


def local_status() -> dict[str, Any]:
    topics = _load_topics()
    return {
        "mode": "offline",
        "provider": "local",
        "network_required": False,
        "knowledge_base": KNOWLEDGE_PATH.name,
        "knowledge_topics": len(topics),
        "llm_runtime": "knowledge_base",
        "message": "Светлана работает полностью локально на версионированной базе знаний. Внешний AI-провайдер для этого endpoint не используется.",
    }
