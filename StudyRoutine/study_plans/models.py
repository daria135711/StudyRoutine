from django.db import models

from exams.models import Exam
from topics.models import Topic


class ExamPreparationPlan(models.Model):
    id_plan_exam = models.AutoField(primary_key=True)
    id_exam = models.OneToOneField(
        Exam,
        on_delete=models.CASCADE,
        db_column='id_exam',
        related_name='preparation_plan',
    )
    plan_data = models.JSONField()
    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ExamPreparationPlan'
        verbose_name = 'Exam Preparation Plan'
        verbose_name_plural = 'Exam Preparation Plans'

    def __str__(self):
        return f'План подготовки — {self.id_exam.title}'


class StudyPlan(models.Model):
    id_plan = models.AutoField(primary_key=True)
    id_topic = models.ForeignKey(
        Topic,
        on_delete=models.DO_NOTHING,
        db_column='id_topic'
    )
    planned_date = models.DateField()
    repetition_number = models.IntegerField()
    is_done = models.BooleanField(blank=True, null=True)

    class Meta:
        db_table = 'StudyPlan'
        verbose_name = 'Study Plan'
        verbose_name_plural = 'Study Plans'

    def __str__(self):
        return f"Plan for Topic {self.id_topic_id} on {self.planned_date}"