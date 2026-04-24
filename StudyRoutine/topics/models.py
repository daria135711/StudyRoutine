from django.db import models
from exams.models import Exam

class Topic(models.Model):
    id_topic = models.AutoField(primary_key=True)
    id_exam = models.ForeignKey(
        Exam,
        on_delete=models.DO_NOTHING,
        db_column='id_exam'
    )
    title = models.TextField()
    description = models.TextField()
    is_complete = models.BooleanField()
    priority = models.IntegerField()

    class Meta:
        db_table = 'Topic'
        verbose_name = 'Topic'
        verbose_name_plural = 'Topics'

    def __str__(self):
        return self.title