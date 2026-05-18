import json

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


@login_required
def home(request):
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
            f'Построен график повторений ({n_plans} записей плана). '
            f'Добавлено задач на сегодня: {n_tasks}.',
        )
        return redirect('exams:home')

    exams = (
        _user_exams(user)
        .prefetch_related('topics')
        .annotate(
            n_topics=Count('topics'),
            n_done=Count('topics', filter=Q(topics__is_complete=True)),
        )
        .order_by('date')
    )

    user_exam_ids = _user_exams(user).values_list('pk', flat=True)
    topics_qs = Topic.objects.filter(id_exam_id__in=user_exam_ids)
    total_topics = topics_qs.count()
    done_topics = topics_qs.filter(is_complete=True).count()

    today_tasks = (
        DailyTask.objects.filter(id_user=user, date=today)
        .select_related('id_topic', 'id_topic__id_exam')
        .order_by('done', 'id_topic__title')
    )

    plans_today = (
        StudyPlan.objects.filter(planned_date=today, id_topic__id_exam_id__in=user_exam_ids)
        .select_related('id_topic', 'id_topic__id_exam')
        .order_by('id_topic__title', 'repetition_number')
    )

    sessions_today = StudySession.objects.filter(
        date=today, id_topic__id_exam_id__in=user_exam_ids
    ).aggregate(total_minutes=Sum('duration_minutes'))
    minutes_today = sessions_today['total_minutes'] or 0

    study_topics = topics_qs.filter(is_complete=False).order_by('title')

    chart_labels_json = json.dumps(['Готово', 'Осталось'], ensure_ascii=False)
    if total_topics:
        chart_data_json = json.dumps([done_topics, total_topics - done_topics])
    else:
        chart_data_json = json.dumps([0, 0])

    context = {
        'exams': exams,
        'today': today,
        'total_topics': total_topics,
        'done_topics': done_topics,
        'today_tasks': today_tasks,
        'plans_today': plans_today,
        'minutes_today': minutes_today,
        'study_topics': study_topics,
        'chart_labels_json': chart_labels_json,
        'chart_data_json': chart_data_json,
    }
    return render(request, 'exams/home.html', context)


@login_required
def exam_add(request):
    user = get_current_user(request)
    form = ExamForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        exam = form.save(commit=False)
        exam.id_user = user
        exam.save()
        messages.success(request, f'Экзамен «{exam.title}» добавлен.')
        return redirect('exams:home')

    return render(request, 'exams/exam_form.html', {'form': form, 'title': 'Новый экзамен'})


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
        return redirect('exams:home')

    return render(
        request,
        'exams/topic_form.html',
        {'form': form, 'exam': exam, 'title': f'Новая тема — {exam.title}'},
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
    return redirect('exams:home')


@login_required
@require_POST
def task_toggle(request, task_id):
    user = get_current_user(request)
    task = get_object_or_404(DailyTask, pk=task_id, id_user=user)
    task.done = not task.done
    task.save(update_fields=['done'])
    return redirect('exams:home')


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
        return redirect('exams:home')

    topic = Topic.objects.filter(pk=topic_id, id_exam__id_user=user).first()
    if topic is None:
        messages.error(request, 'Тема не найдена.')
        return redirect('exams:home')

    StudySession.objects.create(
        id_topic=topic,
        date=timezone.localdate(),
        duration_minutes=minutes,
        completed=True,
    )
    messages.success(request, f'Сохранена сессия: {minutes} мин. — «{topic.title}».')
    return redirect('exams:home')
