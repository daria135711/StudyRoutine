from django import forms

from exams.models import Exam
from topics.models import Topic


class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ('title', 'date', 'difficulty')
        labels = {
            'title': 'Название',
            'date': 'Дата экзамена',
            'difficulty': 'Сложность (1–5)',
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'difficulty': forms.NumberInput(attrs={'min': 1, 'max': 5, 'class': 'form-control'}),
        }


class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ('title', 'description', 'priority')
        labels = {
            'title': 'Название темы',
            'description': 'Описание',
            'priority': 'Приоритет',
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'priority': forms.NumberInput(attrs={'min': 1, 'max': 10, 'class': 'form-control'}),
        }
