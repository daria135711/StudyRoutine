"""
Распределение повторений тем до даты экзамена (шаги за 14, 7, 3, 1 день и в день экзамена).
Чистый Python + ORM; ежедневный пересчёт в проде можно вынести в Celery Beat.
"""
from __future__ import annotations

from datetime import date, timedelta

from django.db import transaction
from django.utils import timezone

from daily_tasks.models import DailyTask
from exams.models import Exam
from study_plans.models import StudyPlan
from topics.models import Topic
from users.models import User

# Дни до экзамена (от большего интервала к дню экзамена)
DAYS_BEFORE_EXAM = (14, 7, 3, 1, 0)


def build_spaced_plans_for_exam(exam: Exam) -> int:
    """
    Для каждой темы экзамена создаёт строки StudyPlan, если плана ещё нет.
    Возвращает количество созданных записей StudyPlan.
    """
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


def sync_today_daily_tasks(user: User, today: date | None = None) -> int:
    """
    Создаёт DailyTask на дату today для пользователя
    по темам, у которых в этот день запланирован повтор.
    """
    today = today or timezone.localdate()
    if user is None:
        return 0
    created = 0
    plans = StudyPlan.objects.filter(planned_date=today).select_related('id_topic')
    for plan in plans:
        _, was_created = DailyTask.objects.get_or_create(
            id_user=user,
            date=today,
            id_topic=plan.id_topic,
            defaults={'done': False},
        )
        if was_created:
            created += 1
    return created
