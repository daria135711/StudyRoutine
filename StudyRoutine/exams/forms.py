from django import forms

from exams.models import Exam
from topics.models import Topic

INPUT_CLASS = 'form-input'
SELECT_CLASS = 'form-select'
TEXTAREA_CLASS = 'form-textarea'


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
            'title': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': INPUT_CLASS}),
            'difficulty': forms.NumberInput(attrs={'min': 1, 'max': 5, 'class': INPUT_CLASS}),
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
            'title': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'description': forms.Textarea(attrs={'rows': 2, 'class': TEXTAREA_CLASS}),
            'priority': forms.NumberInput(attrs={'min': 1, 'max': 10, 'class': INPUT_CLASS}),
        }
