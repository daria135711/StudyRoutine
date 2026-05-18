from django.urls import path

from . import views

app_name = 'exams'

urlpatterns = [
    path('', views.home, name='home'),
    path('exam/add/', views.exam_add, name='exam_add'),
    path('exam/<int:exam_id>/topic/add/', views.topic_add, name='topic_add'),
    path('topic/<int:topic_id>/complete/', views.topic_complete, name='topic_complete'),
    path('task/<int:task_id>/toggle/', views.task_toggle, name='task_toggle'),
    path('session/add/', views.session_add, name='session_add'),
]
