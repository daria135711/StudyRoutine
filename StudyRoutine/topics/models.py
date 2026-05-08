from django.db import models
from django.urls import reverse

from exams.models import Exam


class Topic(models.Model):
    exam = models.ForeignKey(
        Exam, 
        on_delete=models.CASCADE, 
        related_name='topics',
        verbose_name='Экзамен'
    )
    title = models.CharField(max_length=200, verbose_name='Название темы')
    description = models.TextField(blank=True, verbose_name='Описание')
    is_completed = models.BooleanField(default=False, verbose_name='Изучено')
    priority = models.PositiveSmallIntegerField(default=1, verbose_name='Приоритет')
    estimated_time = models.PositiveIntegerField(
        default=60, 
        help_text='В минутах',
        verbose_name='Оценочное время'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['priority', '-created_at']
        verbose_name = 'Тема'
        verbose_name_plural = 'Темы'
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('topic-detail', kwargs={'pk': self.pk})