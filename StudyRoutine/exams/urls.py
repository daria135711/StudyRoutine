from django.urls import path

from . import views

app_name = 'exams'

urlpatterns = [
    path('', views.main, name='main'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('tasks/', views.tasks_today, name='tasks'),
    path('pomodoro/', views.pomodoro, name='pomodoro'),
    path('exams/', views.exam_list, name='exam_list'),
    path('exams/<int:exam_id>/', views.exam_detail, name='exam_detail'),
    path('topics/', views.topic_list, name='topic_list'),
    path('analytics/', views.analytics, name='analytics'),
    path('exam/add/', views.exam_add, name='exam_add'),
    path('exam/<int:exam_id>/edit/', views.exam_edit, name='exam_edit'),
    path('exam/<int:exam_id>/delete/', views.exam_delete, name='exam_delete'),
    path('exam/<int:exam_id>/topic/add/', views.topic_add, name='topic_add'),
    path('topic/<int:topic_id>/edit/', views.topic_edit, name='topic_edit'),
    path('topic/<int:topic_id>/delete/', views.topic_delete, name='topic_delete'),
    path('topic/<int:topic_id>/complete/', views.topic_complete, name='topic_complete'),
    path('task/<int:task_id>/toggle/', views.task_toggle, name='task_toggle'),
    path('session/add/', views.session_add, name='session_add'),
]
