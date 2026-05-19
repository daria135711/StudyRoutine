"""
Распределение повторений и синхронизация задач на сегодня.
"""
from __future__ import annotations

from datetime import date, timedelta

from django.db import transaction
from django.utils import timezone

from daily_tasks.models import DailyTask
from exams.models import Exam
from study_plans.models import ExamPreparationPlan, StudyPlan
from study_plans.personalized import get_today_plan_items
from topics.models import Topic
from users.models import User

DAYS_BEFORE_EXAM = (14, 7, 3, 1, 0)


def build_spaced_plans_for_exam(exam: Exam) -> int:
    """Создаёт строки StudyPlan (интервальные повторы), если персонального плана нет."""
    if ExamPreparationPlan.objects.filter(id_exam=exam).exists():
        return 0
    created = 0
    with transaction.atomic():
        topics = Topic.objects.filter(id_exam=exam)
        for topic in topics:
            if StudyPlan.objects.filter(id_topic=topic).exists():
                continue
            for repetition_number, days_before in enumerate(DAYS_BEFORE_EXAM, start=1):
                planned_date = exam.date - timedelta(days=days_before)
                StudyPlan.objects.create(
                    id_topic=topic,
                    planned_date=planned_date,
                    repetition_number=repetition_number,
                    is_done=False,
                )
                created += 1
    return created


def _sync_from_preparation_plans(user: User, today: date) -> int:
    created = 0
    exams = Exam.objects.filter(id_user=user).prefetch_related('preparation_plan')
    for exam in exams:
        if not hasattr(exam, 'preparation_plan'):
            continue
        for item in get_today_plan_items(exam, today):
            topic = Topic.objects.filter(pk=item['topic_id'], id_exam=exam).first()
            if topic is None:
                continue
            activity_type = item.get('activity_type', '')
            task, was_created = DailyTask.objects.get_or_create(
                id_user=user,
                date=today,
                id_topic=topic,
                activity_type=activity_type,
                defaults={
                    'done': False,
                    'task_title': item.get('title', topic.title),
                    'task_description': item.get('description', ''),
                },
            )
            if was_created:
                created += 1
            else:
                new_title = item.get('title', topic.title)
                new_desc = item.get('description', '')
                fields_to_update = []
                if task.task_title != new_title:
                    task.task_title = new_title
                    fields_to_update.append('task_title')
                if task.task_description != new_desc:
                    task.task_description = new_desc
                    fields_to_update.append('task_description')
                if fields_to_update:
                    task.save(update_fields=fields_to_update)
    return created


def _sync_from_spaced_plans(user: User, today: date) -> int:
    created = 0
    user_exam_ids = Exam.objects.filter(id_user=user).values_list('pk', flat=True)
    plans = StudyPlan.objects.filter(
        planned_date=today,
        id_topic__id_exam_id__in=user_exam_ids,
    ).exclude(
        id_topic__id_exam__preparation_plan__isnull=False,
    ).select_related('id_topic')
    for plan in plans:
        _, was_created = DailyTask.objects.get_or_create(
            id_user=user,
            date=today,
            id_topic=plan.id_topic,
            activity_type='',
            defaults={
                'done': False,
                'task_title': f'Повторение: {plan.id_topic.title}',
                'task_description': f'Повтор №{plan.repetition_number} по интервальному графику.',
            },
        )
        if was_created:
            created += 1
    return created


def sync_today_daily_tasks(user: User, today: date | None = None) -> int:
    """Создаёт или обновляет задачи на сегодня по всем планам пользователя."""
    today = today or timezone.localdate()
    if user is None:
        return 0
    return _sync_from_preparation_plans(user, today) + _sync_from_spaced_plans(user, today)


def sync_all_user_daily_tasks(user: User, today: date | None = None) -> int:
    """Синхронизирует задачи на сегодня для всех экзаменов с планами."""
    return sync_today_daily_tasks(user, today)
