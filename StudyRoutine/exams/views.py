from django.shortcuts import render
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView
)
from .models import Exam

class ExamListView(ListView):
    model = Exam
    template_name = 'exams/list.html'
    context_object_name = 'exams'

class ExamDetailView(DetailView):
    model = Exam
    template_name = 'exams/detail.html'

class ExamCreateView(CreateView):
    model = Exam
    fields = ['name', 'date', 'topics']
    template_name = 'exams/form.html'
    success_url = '/'

class ExamUpdateView(UpdateView):
    model = Exam
    fields = ['name', 'date', 'topics']
    template_name = 'exams/form.html'
    success_url = '/'

class ExamDeleteView(DeleteView):
    model = Exam
    template_name = 'exams/delete_confirm.html'
    success_url = '/'