from django.db import models
from django.urls import reverse

from topics.models import Topic


class DailyTask(models.Model):
    STATUS_CHOICES = [
        ('pending', 'В ожидании'),
        ('in_progress', 'В процессе'),
        ('completed', 'Выполнено'),
        ('skipped', 'Пропущено'),
    ]
    
    topic = models.ForeignKey(
        Topic, 
        on_delete=models.CASCADE, 
        related_name='daily_tasks',
        verbose_name='Тема'
    )
    scheduled_date = models.DateField(verbose_name='Запланированная дата')
    status = models.CharField(
        max_length=15, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name='Статус'
    )
    actual_time_spent = models.PositiveIntegerField(
        default=0, 
        help_text='В минутах',
        verbose_name='Фактическое время'
    )
    notes = models.TextField(blank=True, verbose_name='Заметки')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-scheduled_date', 'status']
        verbose_name = 'Ежедневная задача'
        verbose_name_plural = 'Ежедневные задачи'
        unique_together = ['topic', 'scheduled_date']
    
    def __str__(self):
        return f"{self.topic.title} — {self.scheduled_date}"
    
    def get_absolute_url(self):
        return reverse('dailytask-detail', kwargs={'pk': self.pk})