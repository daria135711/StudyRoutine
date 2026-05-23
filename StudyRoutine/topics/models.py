from django.db import models

from exams.models import Exam
from topics.constants import PRIORITY_CHOICES, PRIORITY_MEDIUM


class Topic(models.Model):
    id_topic = models.AutoField(primary_key=True)
    id_exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        db_column='id_exam',
        related_name='topics',
    )
    title = models.TextField()
    description = models.TextField()
    is_complete = models.BooleanField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)

    class Meta:
        db_table = 'Topic'
        verbose_name = 'Topic'
        verbose_name_plural = 'Topics'

    def __str__(self):
        return self.title


class TopicSubtopic(models.Model):
    SOURCE_USER = 'user'
    SOURCE_GENERATED = 'generated'

    SOURCE_CHOICES = (
        (SOURCE_USER, 'Пользователь'),
        (SOURCE_GENERATED, 'Сгенерировано'),
    )

    id_subtopic = models.AutoField(primary_key=True)
    id_topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        db_column='id_topic',
        related_name='subtopics',
    )
    title = models.TextField()
    description = models.TextField(blank=True)
    is_complete = models.BooleanField(default=False)
    source = models.CharField(max_length=16, choices=SOURCE_CHOICES, default=SOURCE_USER)
    generated_key = models.CharField(max_length=255, blank=True, default='')
    is_deleted = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = 'TopicSubtopic'
        verbose_name = 'Topic Subtopic'
        verbose_name_plural = 'Topic Subtopics'
        ordering = ['sort_order', 'id_subtopic']

    def __str__(self):
        return self.title
