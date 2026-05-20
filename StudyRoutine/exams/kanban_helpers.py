from __future__ import annotations

from django.utils import timezone

from daily_tasks.models import KANBAN_DONE, KANBAN_IN_PROGRESS, KANBAN_TODO, DailyTask, UserDailyTodo


def _format_subtitle(task_date, exam_title: str = '') -> str:
    today = timezone.localdate()
    if task_date == today:
        date_part = 'Сегодня'
    else:
        date_part = task_date.strftime('%d %b')
    if exam_title:
        return f'{date_part} · {exam_title}'
    return date_part


def build_kanban_tasks(plan_tasks, custom_todos) -> dict:
    columns = {
        KANBAN_TODO: [],
        KANBAN_IN_PROGRESS: [],
        KANBAN_DONE: [],
    }
    for task in plan_tasks:
        status = task.kanban_status or (KANBAN_DONE if task.done else KANBAN_TODO)
        if status not in columns:
            status = KANBAN_TODO
        columns[status].append(
            {
                'id': task.pk,
                'type': 'plan',
                'title': task.display_title(),
                'subtitle': _format_subtitle(
                    task.date,
                    task.id_topic.id_exam.title if task.id_topic_id else '',
                ),
                'status': status,
            }
        )
    for todo in custom_todos:
        status = todo.kanban_status or (KANBAN_DONE if todo.done else KANBAN_TODO)
        if status not in columns:
            status = KANBAN_TODO
        columns[status].append(
            {
                'id': todo.pk,
                'type': 'custom',
                'title': todo.title,
                'subtitle': _format_subtitle(todo.date),
                'status': status,
            }
        )
    return columns
