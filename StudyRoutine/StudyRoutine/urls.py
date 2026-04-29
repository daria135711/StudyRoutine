"""
URL configuration for StudyRoutine project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    path('auth/', TemplateView.as_view(template_name='auth.html'), name='auth_page'),
    path('daily-tasks/', TemplateView.as_view(template_name='daily_tasks.html'), name='daily_tasks_page'),
    path('study-plan/', TemplateView.as_view(template_name='study_plan.html'), name='study_plan_page'),
    path('add-exam/', TemplateView.as_view(template_name='add_exam.html'), name='add_exam_page'),
    
    path('exams/', views.exams_list, name='exams_list'),
    path('exams/<int:exam_id>/', views.exam_detail, name='exam_detail'),
    path('stats/', views.stats, name='stats'),
]
