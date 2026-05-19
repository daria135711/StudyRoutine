"""
Получение актуальной информации по теме из Википедии (ru).
При недоступности сети используется локальная генерация на основе названия темы.
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

WIKI_API = 'https://ru.wikipedia.org/w/api.php'
USER_AGENT = 'StudyRoutine/1.0 (educational app)'


def _wiki_get(params: dict[str, str]) -> dict[str, Any] | None:
    query = urllib.parse.urlencode({**params, 'format': 'json'})
    url = f'{WIKI_API}?{query}'
    request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            return json.loads(response.read().decode('utf-8'))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None


def _resolve_page_title(topic_title: str) -> str | None:
    data = _wiki_get(
        {
            'action': 'opensearch',
            'search': topic_title,
            'limit': '1',
            'namespace': '0',
        }
    )
    if not data or len(data) < 2 or not data[1]:
        return topic_title
    return data[1][0]


def _fetch_summary(page_title: str) -> str:
    data = _wiki_get(
        {
            'action': 'query',
            'prop': 'extracts',
            'explaintext': '1',
            'exintro': '0',
            'exsentences': '6',
            'titles': page_title,
        }
    )
    if not data:
        return ''
    pages = data.get('query', {}).get('pages', {})
    for page in pages.values():
        extract = page.get('extract', '')
        if extract:
            return extract.strip()
    return ''


def _fetch_sections(page_title: str) -> list[dict[str, str]]:
    data = _wiki_get(
        {
            'action': 'parse',
            'page': page_title,
            'prop': 'sections',
        }
    )
    if not data:
        return []
    sections = data.get('parse', {}).get('sections', [])
    result = []
    for section in sections[:8]:
        title = (section.get('line') or '').strip()
        if not title or title.lower() in ('см. также', 'примечания', 'литература', 'ссылки'):
            continue
        result.append({'title': title, 'description': f'Раздел «{title}» — ключевой блок программы по теме.'})
    return result


def _split_sentences(text: str, max_count: int = 3) -> list[str]:
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [p.strip() for p in parts if p.strip()][:max_count]


def _extract_concepts(text: str, topic_title: str) -> list[dict[str, str]]:
    concepts: list[dict[str, str]] = []
    patterns = [
        r'([А-ЯЁ][а-яё]+(?:\s+[а-яё]+){0,3})\s+—\s+([^.;]+[.;])',
        r'«([^»]+)»\s*—\s*([^.;]+)',
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            term = match.group(1).strip()
            definition = match.group(2).strip()
            if 3 < len(term) < 80 and len(definition) > 10:
                concepts.append({'term': term, 'definition': definition})
            if len(concepts) >= 5:
                return concepts
    if not concepts:
        concepts = [
            {
                'term': topic_title,
                'definition': (
                    f'Центральное понятие темы «{topic_title}»: базовые определения, '
                    'свойства и связи с соседними разделами курса.'
                ),
            },
            {
                'term': 'Ключевые свойства',
                'definition': (
                    'Набор характерных признаков и закономерностей, '
                    'которые необходимо уметь формулировать и применять на практике.'
                ),
            },
        ]
    return concepts


def fetch_topic_knowledge(topic_title: str, user_description: str = '') -> dict[str, Any]:
    page_title = _resolve_page_title(topic_title)
    summary = _fetch_summary(page_title or topic_title)
    sections = _fetch_sections(page_title or topic_title)

    if not summary:
        base = user_description.strip() or (
            f'Тема «{topic_title}» важна для системной подготовки к экзамену: '
            'требуется понимание определений, связей между понятиями и типовых приёмов решения задач.'
        )
        summary = base

    sentences = _split_sentences(summary, 3)
    description = ' '.join(sentences[:3]) if sentences else summary[:400]

    concepts = _extract_concepts(summary, topic_title)
    theorems = []
    for sentence in sentences:
        lower = sentence.lower()
        if any(word in lower for word in ('теорем', 'лемм', 'формул', 'закон', 'правил')):
            theorems.append({'name': topic_title, 'statement': sentence})
    if not theorems:
        theorems.append(
            {
                'name': f'Основные положения — {topic_title}',
                'statement': (
                    f'Сформулируйте и докажите ключевые утверждения по теме «{topic_title}», '
                    'опираясь на определения и ранее изученный материал.'
                ),
            }
        )

    subtopics = sections[:6]
    if not subtopics:
        subtopics = [
            {'title': 'Введение и определения', 'description': 'Базовые термины и постановка задачи.'},
            {'title': 'Основные методы', 'description': 'Алгоритмы и приёмы, применяемые на практике.'},
            {'title': 'Типовые задачи', 'description': 'Задачи уровня экзамена и разбор ошибок.'},
        ]

    return {
        'summary': summary,
        'description': description,
        'key_concepts': concepts,
        'theorems': theorems[:4],
        'subtopics': subtopics,
        'source': 'wikipedia' if summary and 'важна для системной' not in summary[:80] else 'generated',
    }
