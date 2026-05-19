from django import forms
from django.core.exceptions import ValidationError

from exams.fields import RussianDateField
from exams.models import Exam
from daily_tasks.models import DailyTask
from topics.constants import VALID_PRIORITIES
from topics.models import Topic, TopicSubtopic

INPUT_CLASS = 'form-input'
SELECT_CLASS = 'form-select'
TEXTAREA_CLASS = 'form-textarea'


class ExamForm(forms.ModelForm):
    date = RussianDateField(label='Дата экзамена')

    class Meta:
        model = Exam
        fields = ('title', 'date', 'difficulty')
        labels = {
            'title': 'Название',
            'difficulty': 'Сложность (1–5)',
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'difficulty': forms.NumberInput(attrs={'min': 1, 'max': 5, 'class': INPUT_CLASS}),
        }


class TopicForm(forms.ModelForm):
    priority = forms.CharField(
        label='Приоритет',
        widget=forms.TextInput(
            attrs={
                'class': INPUT_CLASS,
                'placeholder': 'низкий, средний или высокий',
                'list': 'priority-options',
                'autocomplete': 'off',
            }
        ),
        help_text='Укажите только: низкий, средний или высокий.',
    )

    class Meta:
        model = Topic
        fields = ('title', 'description', 'priority')
        labels = {
            'title': 'Название темы',
            'description': 'Описание',
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'description': forms.Textarea(attrs={'rows': 2, 'class': TEXTAREA_CLASS}),
        }

    def clean_priority(self):
        raw = (self.cleaned_data.get('priority') or '').strip().lower()
        if raw not in VALID_PRIORITIES:
            raise ValidationError(
                'Допустимы только значения: низкий, средний, высокий.',
            )
        return raw


class TopicSubtopicForm(forms.ModelForm):
    class Meta:
        model = TopicSubtopic
        fields = ('title', 'description')
        labels = {
            'title': 'Название подтемы',
            'description': 'Описание подтемы',
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': TEXTAREA_CLASS}),
        }


class DailyTaskForm(forms.ModelForm):
    class Meta:
        model = DailyTask
        fields = ('id_topic', 'task_title', 'task_description')
        labels = {
            'id_topic': 'Тема',
            'task_title': 'Задача',
            'task_description': 'Описание',
        }
        widgets = {
            'id_topic': forms.Select(attrs={'class': SELECT_CLASS}),
            'task_title': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'task_description': forms.Textarea(attrs={'rows': 3, 'class': TEXTAREA_CLASS}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['id_topic'].queryset = Topic.objects.filter(id_exam__id_user=user).order_by('title')
        self.fields['task_title'].required = False
        self.fields['task_description'].required = False
