"""Данные аналитики для страницы и live-обновления."""
from __future__ import annotations

from datetime import timedelta

from django.db.models import Count, Q, Sum
from django.utils import timezone

from daily_tasks.models import DailyTask, UserDailyTodo
from exams.models import Exam
from study_sessions.models import StudySession
from topics.models import Topic


def _user_exam_ids(user):
    return list(Exam.objects.filter(id_user=user).values_list('pk', flat=True))


def _tasks_for_day(user, day):
    plan_done = DailyTask.objects.filter(id_user=user, date=day, done=True).count()
    plan_total = DailyTask.objects.filter(id_user=user, date=day).count()
    custom_done = UserDailyTodo.objects.filter(id_user=user, date=day, done=True).count()
    custom_total = UserDailyTodo.objects.filter(id_user=user, date=day).count()
    return {
        'done': plan_done + custom_done,
        'total': plan_total + custom_total,
    }


def build_analytics_payload(user, today=None) -> dict:
    today = today or timezone.localdate()
    user_exam_ids = _user_exam_ids(user)

    total_minutes = (
        StudySession.objects.filter(id_topic__id_exam_id__in=user_exam_ids).aggregate(
            s=Sum('duration_minutes')
        )['s']
        or 0
    )
    total_sessions = StudySession.objects.filter(
        id_topic__id_exam_id__in=user_exam_ids
    ).count()

    minutes_today = (
        StudySession.objects.filter(
            date=today, id_topic__id_exam_id__in=user_exam_ids
        ).aggregate(s=Sum('duration_minutes'))['s']
        or 0
    )

    total_topics = Topic.objects.filter(id_exam_id__in=user_exam_ids).count()
    done_topics = Topic.objects.filter(id_exam_id__in=user_exam_ids, is_complete=True).count()

    today_tasks = _tasks_for_day(user, today)
    tasks_done = today_tasks['done']
    tasks_total = today_tasks['total']
    tasks_pct = round(tasks_done / tasks_total * 100) if tasks_total else 0

    week_start = today - timedelta(days=6)
    week_data = []
    for i in range(7):
        day = week_start + timedelta(days=i)
        mins = (
            StudySession.objects.filter(
                date=day, id_topic__id_exam_id__in=user_exam_ids
            ).aggregate(s=Sum('duration_minutes'))['s']
            or 0
        )
        day_tasks = _tasks_for_day(user, day)
        week_data.append(
            {
                'label': day.strftime('%a'),
                'minutes': mins,
                'tasks_done': day_tasks['done'],
                'tasks_total': day_tasks['total'],
            }
        )

    max_week = max((d['minutes'] for d in week_data), default=1) or 1
    for d in week_data:
        d['height_pct'] = round(d['minutes'] / max_week * 100)
        t_total = d['tasks_total'] or 1
        d['tasks_height_pct'] = round(d['tasks_done'] / t_total * 100) if d['tasks_total'] else 0

    exam_stats = []
    for exam in Exam.objects.filter(id_user=user).annotate(n_topics=Count('topics')):
        mins = (
            StudySession.objects.filter(id_topic__id_exam=exam).aggregate(
                s=Sum('duration_minutes')
            )['s']
            or 0
        )
        exam_stats.append({'title': exam.title, 'minutes': mins})

    max_exam_mins = max((e['minutes'] for e in exam_stats), default=1) or 1
    for e in exam_stats:
        e['width_pct'] = round(e['minutes'] / max_exam_mins * 100) if max_exam_mins else 0

    tasks_remaining = max(tasks_total - tasks_done, 0)
    topics_remaining = max(total_topics - done_topics, 0)

    return {
        'total_minutes': total_minutes,
        'total_sessions': total_sessions,
        'minutes_today': minutes_today,
        'tasks_done': tasks_done,
        'tasks_total': tasks_total,
        'tasks_pct': tasks_pct,
        'done_topics': done_topics,
        'total_topics': total_topics,
        'week_data': week_data,
        'exam_stats': exam_stats,
        'task_chart_labels': ['Выполнено', 'Осталось'],
        'task_chart_data': [tasks_done, tasks_remaining],
        'topic_chart_labels': ['Готово', 'Осталось'],
        'topic_chart_data': [done_topics, topics_remaining],
    }
