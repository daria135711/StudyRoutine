import json
from datetime import timedelta

from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from daily_tasks.models import DailyTask
from exams.forms import ExamForm, TopicForm
from exams.models import Exam
from study_plans.planning import build_spaced_plans_for_exam, sync_today_daily_tasks
from study_plans.models import StudyPlan
from study_sessions.models import StudySession
from topics.models import Topic
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

    today_tasks = list(
        DailyTask.objects.filter(id_user=user, date=today)
        .select_related('id_topic', 'id_topic__id_exam')
        .order_by('done', 'id_topic__title')
    )
    tasks_done = sum(1 for t in today_tasks if t.done)
    tasks_pct = round(tasks_done / len(today_tasks) * 100) if today_tasks else 0

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

    if request.GET.get('build') and request.GET.get('exam'):
        try:
            exam_id = int(request.GET['exam'])
        except (TypeError, ValueError):
            raise Http404
        exam = _user_exam_or_404(user, exam_id)
        n_plans = build_spaced_plans_for_exam(exam)
        n_tasks = sync_today_daily_tasks(user, today)
        messages.success(
            request,
            f'Построен график повторений ({n_plans} записей). '
            f'Добавлено задач на сегодня: {n_tasks}.',
        )
        return redirect('exams:dashboard')

    context = _user_stats(user, today)
    context['active_nav'] = 'dashboard'
    context['plans_today'] = (
        StudyPlan.objects.filter(
            planned_date=today,
            id_topic__id_exam_id__in=_user_exams(user).values_list('pk', flat=True),
        )
        .select_related('id_topic', 'id_topic__id_exam')
        .order_by('id_topic__title', 'repetition_number')
    )
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
        .prefetch_related('topics')
        .annotate(
            n_topics=Count('topics'),
            n_done=Count('topics', filter=Q(topics__is_complete=True)),
        ),
        pk=exam_id,
    )
    _annotate_exams([exam], today)
    return render(
        request,
        'exams/exam_detail.html',
        {'exam': exam, 'active_nav': 'exams', 'today': today},
    )


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
    user_exam_ids = list(_user_exams(user).values_list('pk', flat=True))

    total_minutes = (
        StudySession.objects.filter(id_topic__id_exam_id__in=user_exam_ids).aggregate(
            s=Sum('duration_minutes')
        )['s']
        or 0
    )
    total_sessions = StudySession.objects.filter(
        id_topic__id_exam_id__in=user_exam_ids
    ).count()

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
        week_data.append({'label': day.strftime('%a'), 'minutes': mins})

    max_week = max((d['minutes'] for d in week_data), default=1) or 1
    for d in week_data:
        d['height_pct'] = round(d['minutes'] / max_week * 100)

    exam_stats = []
    for exam in _user_exams(user).annotate(n_topics=Count('topics')):
        mins = (
            StudySession.objects.filter(id_topic__id_exam=exam).aggregate(
                s=Sum('duration_minutes')
            )['s']
            or 0
        )
        exam_stats.append({'exam': exam, 'minutes': mins})

    max_exam_mins = max((e['minutes'] for e in exam_stats), default=1) or 1
    for e in exam_stats:
        e['width_pct'] = round(e['minutes'] / max_exam_mins * 100) if max_exam_mins else 0

    stats = _user_stats(user, today)
    return render(
        request,
        'exams/analytics.html',
        {
            'active_nav': 'analytics',
            'total_minutes': total_minutes,
            'total_sessions': total_sessions,
            'week_data': week_data,
            'exam_stats': exam_stats,
            **stats,
        },
    )


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
        topic.delete()
        messages.success(request, f'Тема «{title}» удалена.')
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
@require_POST
def task_toggle(request, task_id):
    user = get_current_user(request)
    task = get_object_or_404(DailyTask, pk=task_id, id_user=user)
    task.done = not task.done
    task.save(update_fields=['done'])
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
