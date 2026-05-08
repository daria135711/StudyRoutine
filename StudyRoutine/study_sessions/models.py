from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model

from topics.models import Topic

User = get_user_model()


class StudySession(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='study_sessions',
        verbose_name='Пользователь'
    )
    topic = models.ForeignKey(
        Topic, 
        on_delete=models.CASCADE, 
        related_name='sessions',
        verbose_name='Тема',
        null=True, 
        blank=True
    )
    start_time = models.DateTimeField(auto_now_add=True, verbose_name='Начало')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='Конец')
    duration_minutes = models.PositiveIntegerField(default=0, verbose_name='Длительность')
    notes = models.TextField(blank=True, verbose_name='Заметки')
    
    class Meta:
        ordering = ['-start_time']
        verbose_name = 'Сессия обучения'
        verbose_name_plural = 'Сессии обучения'
    
    def __str__(self):
        return f"Сессия {self.user.username} — {self.start_time.strftime('%d.%m %H:%M')}"
    
    def get_absolute_url(self):
        return reverse('studysession-detail', kwargs={'pk': self.pk})