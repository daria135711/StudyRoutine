"""
Персонализированный план подготовки к экзамену:
- приоритизация тем;
- чередование теории и практики;
- расписание по дням;
- контент из Википедии.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from django.db import transaction
from django.utils import timezone

from exams.models import Exam
from study_plans.knowledge_fetcher import fetch_topic_knowledge
from study_plans.models import ExamPreparationPlan, StudyPlan
from topics.constants import PRIORITY_ORDER
from topics.models import Topic
from topics.subtopics import sync_generated_subtopics

ACTIVITY_SEQUENCE = (
    ('theory', 'Теория'),
    ('practice_basic', 'Практика (базовые задачи)'),
    ('theory_advanced', 'Углублённая теория'),
    ('practice_exam', 'Практика (экзаменационные задачи)'),
)

ACTIVITY_LABELS = dict(ACTIVITY_SEQUENCE)


def _sorted_topics(exam: Exam) -> list[Topic]:
    topics = list(Topic.objects.filter(id_exam=exam))
    return sorted(
        topics,
        key=lambda t: (PRIORITY_ORDER.get(t.priority, 1), t.title.lower()),
    )


def _practice_tasks(topic_title: str, level: str) -> list[str]:
    if level == 'basic':
        return [
            f'Решите 3–5 базовых задач по теме «{topic_title}» без подсказок.',
            f'Составьте шпаргалку с формулами и типовыми шагами для «{topic_title}».',
            f'Объясните решение одной задачи вслух, как на экзамене.',
        ]
    return [
        f'Решите 2–3 задачи повышенной сложности по «{topic_title}» за ограниченное время.',
        f'Разберите типовые ловушки и частые ошибки в задачах на «{topic_title}».',
        f'Смоделируйте экзаменационный билет по теме «{topic_title}» (45–60 мин).',
    ]


def _build_topic_block(topic: Topic, knowledge: dict[str, Any]) -> dict[str, Any]:
    title = topic.title
    return {
        'topic_id': topic.pk,
        'title': title,
        'priority': topic.priority,
        'description': knowledge['description'],
        'theory': {
            'key_concepts': knowledge['key_concepts'],
            'theorems': knowledge['theorems'],
            'subtopics': knowledge['subtopics'],
        },
        'practice_basic': _practice_tasks(title, 'basic'),
        'practice_advanced': _practice_tasks(title, 'exam'),
        'advanced_theory_notes': (
            f'Углублённо изучите связи «{title}» с соседними темами, '
            'докажите основные утверждения и разберите нестандартные формулировки.'
        ),
        'knowledge_source': knowledge.get('source', 'generated'),
    }


def _slot_content(topic_block: dict[str, Any], activity_type: str) -> tuple[str, str]:
    title = topic_block['title']
    if activity_type == 'theory':
        concepts = topic_block['theory']['key_concepts'][:2]
        hint = '; '.join(c['term'] for c in concepts)
        return (
            f'{title}: теория',
            f'Изучите определения и подтемы. Ключевое: {hint}.',
        )
    if activity_type == 'practice_basic':
        task = topic_block['practice_basic'][0]
        return (f'{title}: базовая практика', task)
    if activity_type == 'theory_advanced':
        return (
            f'{title}: углублённая теория',
            topic_block['advanced_theory_notes'],
        )
    task = topic_block['practice_advanced'][0]
    return (f'{title}: экзаменационная практика', task)


def _build_schedule(
    topic_blocks: list[dict[str, Any]],
    start: date,
    end: date,
) -> list[dict[str, Any]]:
    slots: list[tuple[dict[str, Any], str]] = []
    for block in topic_blocks:
        for activity_type, _ in ACTIVITY_SEQUENCE:
            slots.append((block, activity_type))

    total_days = max((end - start).days, 1)
    if not slots:
        return []

    schedule: list[dict[str, Any]] = []
    day_index = 0
    slot_index = 0
    total_slots = len(slots)

    while slot_index < total_slots and day_index < total_days:
        current_date = start + timedelta(days=day_index)
        items_per_day = 1
        if total_days <= total_slots // 2:
            items_per_day = 2

        day_items = []
        for _ in range(items_per_day):
            if slot_index >= total_slots:
                break
            block, activity_type = slots[slot_index]
            slot_title, slot_desc = _slot_content(block, activity_type)
            day_items.append(
                {
                    'topic_id': block['topic_id'],
                    'topic_title': block['title'],
                    'priority': block['priority'],
                    'activity_type': activity_type,
                    'activity_label': ACTIVITY_LABELS[activity_type],
                    'title': slot_title,
                    'description': slot_desc,
                }
            )
            slot_index += 1

        if day_items:
            schedule.append(
                {
                    'date': current_date.isoformat(),
                    'day_number': day_index + 1,
                    'items': day_items,
                }
            )
        day_index += 1

    while slot_index < total_slots:
        last_day = schedule[-1] if schedule else None
        block, activity_type = slots[slot_index]
        slot_title, slot_desc = _slot_content(block, activity_type)
        item = {
            'topic_id': block['topic_id'],
            'topic_title': block['title'],
            'priority': block['priority'],
            'activity_type': activity_type,
            'activity_label': ACTIVITY_LABELS[activity_type],
            'title': slot_title,
            'description': slot_desc,
        }
        if last_day:
            last_day['items'].append(item)
        else:
            schedule.append(
                {
                    'date': start.isoformat(),
                    'day_number': 1,
                    'items': [item],
                }
            )
        slot_index += 1

    return schedule


def build_personalized_plan(exam: Exam, today: date | None = None) -> ExamPreparationPlan:
    today = today or timezone.localdate()
    topics = _sorted_topics(exam)
    if not topics:
        raise ValueError('Добавьте хотя бы одну тему перед построением плана.')

    topic_blocks = []
    for topic in topics:
        knowledge = fetch_topic_knowledge(topic.title, topic.description or '')
        block = _build_topic_block(topic, knowledge)
        sync_generated_subtopics(topic, block['theory']['subtopics'])
        topic_blocks.append(block)

    study_until = exam.date - timedelta(days=1)
    if study_until < today:
        study_until = exam.date

    schedule = _build_schedule(topic_blocks, today, study_until)
    plan_data = {
        'exam_id': exam.pk,
        'exam_title': exam.title,
        'exam_date': exam.date.isoformat(),
        'generated_for_date': today.isoformat(),
        'method_note': (
            'План построен по методике чередования: теория → базовая практика → '
            'углублённая теория → экзаменационная практика. Темы отсортированы по приоритету.'
        ),
        'topics': topic_blocks,
        'schedule': schedule,
    }

    with transaction.atomic():
        StudyPlan.objects.filter(id_topic__id_exam=exam).delete()
        ExamPreparationPlan.objects.filter(id_exam=exam).delete()
        plan = ExamPreparationPlan.objects.create(id_exam=exam, plan_data=plan_data)
    return plan


def get_today_plan_items(exam: Exam, today: date) -> list[dict[str, Any]]:
    try:
        plan = exam.preparation_plan
    except ExamPreparationPlan.DoesNotExist:
        return []
    items = []
    for day in plan.plan_data.get('schedule', []):
        if day.get('date') == today.isoformat():
            items.extend(day.get('items', []))
    return items
