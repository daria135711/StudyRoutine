from django.forms import ModelForm
from .models import Exam

class ExamForm(ModelForm):
    class Meta:
        model = Exam
        fields = ['name', 'date', 'topics']