import json
from datetime import timedelta

from django.contrib import messages
from django.db import transaction
from django.db import connection
from django.db.models import Count, Q, Sum
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from daily_tasks.models import (
    KANBAN_DONE,
    KANBAN_IN_PROGRESS,
    KANBAN_TODO,
    DailyTask,
    UserDailyTodo,
)
from exams.forms import ExamForm, TopicForm, TopicSubtopicForm
from exams.analytics_data import build_analytics_payload
from exams.kanban_helpers import build_kanban_tasks
from exams.models import Exam
from study_plans.models import ExamPreparationPlan, StudyPlan
from study_plans.personalized import build_personalized_plan, get_today_plan_items
from study_plans.planning import sync_all_user_daily_tasks, sync_today_daily_tasks
from study_sessions.models import StudySession
from topics.models import Topic, TopicSubtopic
from users.auth_helpers import get_current_user, login_required


def _user_exams(user):
    return Exam.objects.filter(id_user=user)


def _user_exam_or_404(user, exam_id):
    return get_object_or_404(_user_exams(user), pk=exam_id)


def _annotate_exams(exams, today):
    for exam in exams:
        exam.days_left = max((exam.date - today).days, 0)
        if exam.difficulty <= 2:
            exam.difficulty_label = 'Лёгкая'
            exam.difficulty_class = 'diff-easy'
        elif exam.difficulty <= 3:
            exam.difficulty_label = 'Средняя'
            exam.difficulty_class = 'diff-medium'
        else:
            exam.difficulty_label = 'Сложная'
            exam.difficulty_class = 'diff-hard'
    return exams


def _user_stats(user, today):
    user_exam_ids = _user_exams(user).values_list('pk', flat=True)
    topics_qs = Topic.objects.filter(id_exam_id__in=user_exam_ids)
    total_topics = topics_qs.count()
    done_topics = topics_qs.filter(is_complete=True).count()

    sync_all_user_daily_tasks(user, today)
    today_tasks = list(
        DailyTask.objects.filter(id_user=user, date=today)
        .select_related('id_topic', 'id_topic__id_exam')
        .order_by('done', 'id_topic__id_exam__date', 'id_topic__title')
    )
    custom_todos = list(UserDailyTodo.objects.filter(id_user=user, date=today).order_by('id_todo'))
    all_today = today_tasks + custom_todos
    tasks_done = sum(1 for t in all_today if t.done)
    tasks_pct = round(tasks_done / len(all_today) * 100) if all_today else 0

    sessions_today = StudySession.objects.filter(
        date=today, id_topic__id_exam_id__in=user_exam_ids
    ).aggregate(total_minutes=Sum('duration_minutes'), total_sessions=Count('id_session'))
    minutes_today = sessions_today['total_minutes'] or 0
    pomodoro_today = sessions_today['total_sessions'] or 0

    exams = list(
        _user_exams(user)
        .annotate(
            n_topics=Count('topics'),
            n_done=Count('topics', filter=Q(topics__is_complete=True)),
        )
        .order_by('date')
    )
    _annotate_exams(exams, today)

    return {
        'exams': exams,
        'today': today,
        'total_topics': total_topics,
        'done_topics': done_topics,
        'today_tasks': today_tasks,
        'custom_todos': custom_todos,
        'tasks_total': len(all_today),
        'tasks_done': tasks_done,
        'tasks_pct': tasks_pct,
        'minutes_today': minutes_today,
        'pomodoro_today': pomodoro_today,
        'study_topics': topics_qs.filter(is_complete=False).order_by('title'),
        'chart_labels_json': json.dumps(['Готово', 'Осталось'], ensure_ascii=False),
        'chart_data_json': json.dumps(
            [done_topics, total_topics - done_topics] if total_topics else [0, 0]
        ),
    }


def main(request):
    return render(request, 'pages/main.html')


@login_required
def dashboard(request):
    user = get_current_user(request)
    today = timezone.localdate()

    context = _user_stats(user, today)
    context['active_nav'] = 'dashboard'
    plans_today = []
    for exam in _user_exams(user).select_related('preparation_plan'):
        if hasattr(exam, 'preparation_plan'):
            for item in get_today_plan_items(exam, today):
                plans_today.append(
                    {
                        'exam': exam,
                        'topic_title': item.get('topic_title', ''),
                        'activity_label': item.get('activity_label', ''),
                        'description': item.get('description', ''),
                    }
                )
    if not plans_today:
        for plan in StudyPlan.objects.filter(
            planned_date=today,
            id_topic__id_exam_id__in=_user_exams(user).values_list('pk', flat=True),
        ).exclude(id_topic__id_exam__preparation_plan__isnull=False).select_related(
            'id_topic', 'id_topic__id_exam'
        ):
            plans_today.append(
                {
                    'exam': plan.id_topic.id_exam,
                    'topic_title': plan.id_topic.title,
                    'activity_label': f'Повтор №{plan.repetition_number}',
                    'description': '',
                }
            )
    context['plans_today'] = plans_today
    context['kanban_columns'] = build_kanban_tasks(context['today_tasks'], context['custom_todos'])
    context['kanban_json'] = json.dumps(context['kanban_columns'], ensure_ascii=False)
    return render(request, 'exams/dashboard.html', context)


@login_required
def tasks_today(request):
    user = get_current_user(request)
    today = timezone.localdate()
    context = _user_stats(user, today)
    context['active_nav'] = 'tasks'
    return render(request, 'exams/tasks.html', context)


@login_required
def pomodoro(request):
    user = get_current_user(request)
    today = timezone.localdate()
    context = _user_stats(user, today)
    context['active_nav'] = 'pomodoro'
    return render(request, 'exams/pomodoro.html', context)


@login_required
def exam_list(request):
    user = get_current_user(request)
    today = timezone.localdate()
    exams = list(
        _user_exams(user)
        .prefetch_related('topics')
        .annotate(
            n_topics=Count('topics'),
            n_done=Count('topics', filter=Q(topics__is_complete=True)),
        )
        .order_by('date')
    )
    _annotate_exams(exams, today)
    return render(
        request,
        'exams/exam_list.html',
        {'exams': exams, 'active_nav': 'exams', 'today': today},
    )


@login_required
def exam_detail(request, exam_id):
    user = get_current_user(request)
    today = timezone.localdate()
    exam = get_object_or_404(
        _user_exams(user)
        .prefetch_related('topics', 'topics__subtopics')
        .select_related('preparation_plan')
        .annotate(
            n_topics=Count('topics'),
            n_done=Count('topics', filter=Q(topics__is_complete=True)),
        ),
        pk=exam_id,
    )
    _annotate_exams([exam], today)
    preparation_plan = getattr(exam, 'preparation_plan', None)
    return render(
        request,
        'exams/exam_detail.html',
        {
            'exam': exam,
            'active_nav': 'exams',
            'today': today,
            'preparation_plan': preparation_plan,
            'has_preparation_plan': preparation_plan is not None,
        },
    )


@login_required
@require_POST
def exam_build_plan(request, exam_id):
    user = get_current_user(request)
    today = timezone.localdate()
    exam = _user_exam_or_404(user, exam_id)
    has_plan = ExamPreparationPlan.objects.filter(id_exam=exam).exists()
    confirm = request.POST.get('confirm') == '1'

    if has_plan and not confirm:
        messages.warning(
            request,
            'У этого экзамена уже есть план. Подтвердите пересоздание, чтобы продолжить.',
        )
        url = reverse('exams:exam_detail', kwargs={'exam_id': exam.pk})
        return redirect(f'{url}?rebuild=1')

    if not exam.topics.exists():
        messages.error(request, 'Добавьте хотя бы одну тему, затем постройте план.')
        return redirect('exams:exam_detail', exam_id=exam.pk)

    try:
        build_personalized_plan(exam, today)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect('exams:exam_detail', exam_id=exam.pk)

    n_tasks = sync_today_daily_tasks(user, today)
    messages.success(
        request,
        f'Персональный план подготовки создан. Задач на сегодня: {n_tasks}.',
    )
    return redirect('exams:exam_detail', exam_id=exam.pk)


@login_required
def topic_list(request):
    user = get_current_user(request)
    user_exam_ids = _user_exams(user).values_list('pk', flat=True)
    exam_filter_raw = request.GET.get('exam', '')
    exam_filter = int(exam_filter_raw) if exam_filter_raw.isdigit() else None
    topics = Topic.objects.filter(id_exam_id__in=user_exam_ids).select_related('id_exam')
    if exam_filter:
        topics = topics.filter(id_exam_id=exam_filter)
    topics = topics.order_by('id_exam__title', 'title')
    total = topics.count()
    done = topics.filter(is_complete=True).count()
    return render(
        request,
        'exams/topic_list.html',
        {
            'topics': topics,
            'exams': _user_exams(user).order_by('title'),
            'exam_filter': exam_filter,
            'total_topics': total,
            'done_topics': done,
            'active_nav': 'topics',
        },
    )


@login_required
def analytics(request):
    user = get_current_user(request)
    today = timezone.localdate()
    sync_all_user_daily_tasks(user, today)
    payload = build_analytics_payload(user, today)
    stats = _user_stats(user, today)
    return render(
        request,
        'exams/analytics.html',
        {
            'active_nav': 'analytics',
            'task_chart_labels_json': json.dumps(payload['task_chart_labels'], ensure_ascii=False),
            'task_chart_data_json': json.dumps(payload['task_chart_data']),
            **payload,
            **stats,
        },
    )


@login_required
def analytics_data(request):
    user = get_current_user(request)
    today = timezone.localdate()
    sync_all_user_daily_tasks(user, today)
    payload = build_analytics_payload(user, today)
    return JsonResponse({'ok': True, **payload})


@login_required
def exam_add(request):
    user = get_current_user(request)
    form = ExamForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        exam = form.save(commit=False)
        exam.id_user = user
        exam.save()
        messages.success(request, f'Экзамен «{exam.title}» добавлен.')
        return redirect('exams:exam_detail', exam_id=exam.pk)

    return render(
        request,
        'exams/exam_form.html',
        {'form': form, 'title': 'Новый экзамен', 'active_nav': 'exam_add'},
    )


@login_required
def exam_edit(request, exam_id):
    user = get_current_user(request)
    exam = _user_exam_or_404(user, exam_id)
    form = ExamForm(request.POST or None, instance=exam)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Экзамен «{exam.title}» обновлён.')
        return redirect('exams:exam_detail', exam_id=exam.pk)

    return render(
        request,
        'exams/exam_form.html',
        {'form': form, 'title': f'Редактировать — {exam.title}', 'active_nav': 'exams', 'exam': exam},
    )


@login_required
def exam_delete(request, exam_id):
    user = get_current_user(request)
    exam = _user_exam_or_404(user, exam_id)
    if request.method == 'POST':
        title = exam.title
        exam.delete()
        messages.success(request, f'Экзамен «{title}» удалён.')
        return redirect('exams:exam_list')
    return render(
        request,
        'exams/exam_confirm_delete.html',
        {'exam': exam, 'active_nav': 'exams'},
    )


@login_required
def topic_add(request, exam_id):
    user = get_current_user(request)
    exam = _user_exam_or_404(user, exam_id)
    form = TopicForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        topic = form.save(commit=False)
        topic.id_exam = exam
        topic.is_complete = False
        if not topic.description:
            topic.description = ''
        topic.save()
        messages.success(request, f'Тема «{topic.title}» добавлена.')
        return redirect('exams:exam_detail', exam_id=exam.pk)

    return render(
        request,
        'exams/topic_form.html',
        {'form': form, 'exam': exam, 'title': f'Новая тема — {exam.title}', 'active_nav': 'topics'},
    )


@login_required
def topic_edit(request, topic_id):
    user = get_current_user(request)
    topic = get_object_or_404(
        Topic.objects.select_related('id_exam'),
        pk=topic_id,
        id_exam__id_user=user,
    )
    form = TopicForm(request.POST or None, instance=topic)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Тема «{topic.title}» обновлена.')
        return redirect('exams:topic_list')

    return render(
        request,
        'exams/topic_form.html',
        {
            'form': form,
            'exam': topic.id_exam,
            'title': f'Редактировать — {topic.title}',
            'active_nav': 'topics',
            'topic': topic,
        },
    )


@login_required
def topic_delete(request, topic_id):
    user = get_current_user(request)
    topic = get_object_or_404(
        Topic.objects.select_related('id_exam'),
        pk=topic_id,
        id_exam__id_user=user,
    )
    exam = topic.id_exam
    
    if request.method == 'POST':
        title = topic.title
        
        # Удаляем связанные DailyTask
        deleted_tasks = DailyTask.objects.filter(id_topic=topic).delete()
        print(f"Удалено DailyTask: {deleted_tasks}")
        
        # Удаляем связанные StudySession
        from study_sessions.models import StudySession
        StudySession.objects.filter(id_topic=topic).delete()
        
        # Удаляем связанные StudyPlan
        from study_plans.models import StudyPlan
        StudyPlan.objects.filter(id_topic=topic).delete()
        
        # Удаляем подтемы
        topic.subtopics.all().delete()
        
        # Теперь удаляем тему
        topic.delete()
        
        messages.success(request, f'Тема «{title}» и все связанные данные удалены.')
        return redirect('exams:exam_detail', exam_id=exam.pk)
    
    return render(
        request,
        'exams/topic_confirm_delete.html',
        {'topic': topic, 'exam': exam, 'active_nav': 'topics'},
    )

@login_required
@require_POST
def topic_complete(request, topic_id):
    user = get_current_user(request)
    topic = get_object_or_404(
        Topic.objects.select_related('id_exam'),
        pk=topic_id,
        id_exam__id_user=user,
    )
    topic.is_complete = True
    topic.save(update_fields=['is_complete'])
    messages.success(request, f'Тема «{topic.title}» отмечена как изученная.')
    next_url = request.POST.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('exams:topic_list')


@login_required
def subtopic_add(request, topic_id):
    user = get_current_user(request)
    topic = get_object_or_404(Topic.objects.select_related('id_exam'), pk=topic_id, id_exam__id_user=user)
    form = TopicSubtopicForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        subtopic = form.save(commit=False)
        subtopic.id_topic = topic
        subtopic.is_complete = False
        subtopic.source = TopicSubtopic.SOURCE_USER
        if not subtopic.description:
            subtopic.description = ''
        max_order = (
            TopicSubtopic.objects.filter(id_topic=topic, is_deleted=False)
            .order_by('-sort_order')
            .values_list('sort_order', flat=True)
            .first()
            or 0
        )
        subtopic.sort_order = max_order + 1
        subtopic.save()
        messages.success(request, f'Подтема «{subtopic.title}» добавлена.')
        return redirect('exams:exam_detail', exam_id=topic.id_exam.pk)

    return render(
        request,
        'exams/subtopic_form.html',
        {'form': form, 'topic': topic, 'title': f'Новая подтема — {topic.title}', 'active_nav': 'topics'},
    )


@login_required
def subtopic_edit(request, subtopic_id):
    user = get_current_user(request)
    subtopic = get_object_or_404(
        TopicSubtopic.objects.select_related('id_topic__id_exam'),
        pk=subtopic_id,
        id_topic__id_exam__id_user=user,
    )
    form = TopicSubtopicForm(request.POST or None, instance=subtopic)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Подтема «{subtopic.title}» обновлена.')
        return redirect('exams:exam_detail', exam_id=subtopic.id_topic.id_exam.pk)

    return render(
        request,
        'exams/subtopic_form.html',
        {
            'form': form,
            'topic': subtopic.id_topic,
            'title': f'Редактировать — {subtopic.title}',
            'active_nav': 'topics',
            'subtopic': subtopic,
        },
    )


@login_required
def subtopic_delete(request, subtopic_id):
    user = get_current_user(request)
    subtopic = get_object_or_404(
        TopicSubtopic.objects.select_related('id_topic__id_exam'),
        pk=subtopic_id,
        id_topic__id_exam__id_user=user,
    )
    exam = subtopic.id_topic.id_exam
    if request.method == 'POST':
        title = subtopic.title
        subtopic.delete()
        messages.success(request, f'Подтема «{title}» удалена.')
        return redirect('exams:exam_detail', exam_id=exam.pk)
    return render(
        request,
        'exams/subtopic_confirm_delete.html',
        {'subtopic': subtopic, 'exam': exam, 'active_nav': 'topics'},
    )


@login_required
@require_POST
def subtopic_complete(request, subtopic_id):
    user = get_current_user(request)
    subtopic = get_object_or_404(
        TopicSubtopic.objects.select_related('id_topic__id_exam'),
        pk=subtopic_id,
        id_topic__id_exam__id_user=user,
    )
    subtopic.is_complete = True
    subtopic.save(update_fields=['is_complete'])
    messages.success(request, f'Подтема «{subtopic.title}» отмечена как изученная.')
    next_url = request.POST.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('exams:topic_list')


@login_required
@require_POST
def task_toggle(request, task_id):
    user = get_current_user(request)
    task = get_object_or_404(DailyTask, pk=task_id, id_user=user)
    task.done = not task.done
    task.kanban_status = KANBAN_DONE if task.done else KANBAN_TODO
    task.save(update_fields=['done', 'kanban_status'])
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'ok': True, 'done': task.done})
    if task.done:
        label = task.task_title or task.id_topic.title
        messages.success(request, f'Задача «{label}» выполнена.')
    else:
        messages.info(request, 'Отметка снята.')
    next_url = request.POST.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('exams:tasks')


@login_required
@require_POST
def session_add(request):
    user = get_current_user(request)
    topic_id = request.POST.get('topic_id')
    minutes = request.POST.get('minutes', '25')
    try:
        topic_id = int(topic_id)
        minutes = int(minutes)
    except (TypeError, ValueError):
        messages.error(request, 'Укажите тему и длительность.')
        next_url = request.POST.get('next')
        return redirect(next_url if next_url else 'exams:pomodoro')

    topic = Topic.objects.filter(pk=topic_id, id_exam__id_user=user).first()
    if topic is None:
        messages.error(request, 'Тема не найдена.')
        next_url = request.POST.get('next')
        return redirect(next_url if next_url else 'exams:pomodoro')

    StudySession.objects.create(
        id_topic=topic,
        date=timezone.localdate(),
        duration_minutes=minutes,
        completed=True,
    )
    messages.success(request, f'Сохранена сессия: {minutes} мин. — «{topic.title}».')
    next_url = request.POST.get('next')
    return redirect(next_url if next_url else 'exams:pomodoro')


VALID_KANBAN = {KANBAN_TODO, KANBAN_IN_PROGRESS, KANBAN_DONE}


@login_required
@require_POST
def kanban_update_status(request):
    user = get_current_user(request)
    task_type = request.POST.get('task_type', '')
    try:
        task_id = int(request.POST.get('task_id', ''))
    except (TypeError, ValueError):
        return JsonResponse({'ok': False, 'error': 'Некорректный id'}, status=400)
    status = request.POST.get('status', '')
    if status not in VALID_KANBAN:
        return JsonResponse({'ok': False, 'error': 'Некорректный статус'}, status=400)

    if task_type == 'plan':
        task = get_object_or_404(DailyTask, pk=task_id, id_user=user)
        task.apply_kanban_status(status)
        task.save(update_fields=['kanban_status', 'done'])
    elif task_type == 'custom':
        todo = get_object_or_404(UserDailyTodo, pk=task_id, id_user=user)
        todo.apply_kanban_status(status)
        todo.save(update_fields=['kanban_status', 'done'])
    else:
        return JsonResponse({'ok': False, 'error': 'Некорректный тип'}, status=400)

    return JsonResponse({'ok': True, 'status': status, 'done': status == KANBAN_DONE})


@login_required
@require_POST
def custom_todo_add(request):
    user = get_current_user(request)
    title = (request.POST.get('title') or '').strip()
    if not title:
        messages.error(request, 'Введите название задачи.')
        return redirect('exams:tasks')
    task_date = request.POST.get('date') or timezone.localdate().isoformat()
    try:
        from datetime import datetime

        parsed_date = datetime.strptime(task_date, '%Y-%m-%d').date()
    except ValueError:
        parsed_date = timezone.localdate()
    description = (request.POST.get('description') or '').strip()
    UserDailyTodo.objects.create(
        id_user=user,
        date=parsed_date,
        title=title,
        description=description,
        done=False,
        kanban_status=KANBAN_TODO,
    )
    messages.success(request, f'Задача «{title}» добавлена.')
    next_url = request.POST.get('next')
    return redirect(next_url if next_url else 'exams:tasks')


@login_required
@require_POST
def custom_todo_toggle(request, todo_id):
    user = get_current_user(request)
    todo = get_object_or_404(UserDailyTodo, pk=todo_id, id_user=user)
    todo.done = not todo.done
    todo.kanban_status = KANBAN_DONE if todo.done else KANBAN_TODO
    todo.save(update_fields=['done', 'kanban_status'])
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        next_url = request.POST.get('next')
        return redirect(next_url if next_url else 'exams:tasks')
    return JsonResponse({'ok': True, 'done': todo.done})


@login_required
@require_POST
def custom_todo_delete(request, todo_id):
    user = get_current_user(request)
    todo = get_object_or_404(UserDailyTodo, pk=todo_id, id_user=user)
    title = todo.title
    todo.delete()
    messages.success(request, f'Задача «{title}» удалена.')
    next_url = request.POST.get('next')
    return redirect(next_url if next_url else 'exams:tasks')
