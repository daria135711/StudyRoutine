"""Синхронизация подтем плана с базой данных."""
from __future__ import annotations

import hashlib
from typing import Any

from topics.models import Topic, TopicSubtopic


def generated_key(title: str) -> str:
    normalized = (title or '').strip().lower()
    return hashlib.md5(normalized.encode('utf-8')).hexdigest()


def sync_generated_subtopics(topic: Topic, generated_list: list[dict[str, Any]]) -> None:
    """Добавляет новые сгенерированные подтемы, не трогает пользовательские и удалённые."""
    existing = {
        s.generated_key: s
        for s in TopicSubtopic.objects.filter(
            id_topic=topic,
            source=TopicSubtopic.SOURCE_GENERATED,
        )
    }
    max_order = (
        TopicSubtopic.objects.filter(id_topic=topic, is_deleted=False)
        .order_by('-sort_order')
        .values_list('sort_order', flat=True)
        .first()
        or 0
    )
    for item in generated_list:
        title = (item.get('title') or '').strip()
        if not title:
            continue
        key = generated_key(title)
        if key in existing:
            sub = existing[key]
            if not sub.is_deleted and not sub.description and item.get('description'):
                sub.description = item.get('description', '')
                sub.save(update_fields=['description'])
            continue
        max_order += 1
        TopicSubtopic.objects.create(
            id_topic=topic,
            title=title,
            description=item.get('description', ''),
            source=TopicSubtopic.SOURCE_GENERATED,
            generated_key=key,
            is_deleted=False,
            sort_order=max_order,
        )


def get_visible_subtopics(topic: Topic):
    return TopicSubtopic.objects.filter(id_topic=topic, is_deleted=False)
