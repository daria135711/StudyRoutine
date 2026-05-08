from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class Exam(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Лёгкий'),
        ('medium', 'Средний'),
        ('hard', 'Сложный'),
    ]
    
    title = models.CharField(max_length=200, verbose_name='Название экзамена')
    exam_date = models.DateField(verbose_name='Дата экзамена')
    difficulty = models.CharField(
        max_length=10, 
        choices=DIFFICULTY_CHOICES, 
        default='medium',
        verbose_name='Сложность'
    )
    description = models.TextField(blank=True, verbose_name='Описание')
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='exams',
        verbose_name='Пользователь'
    )
    
    class Meta:
        ordering = ['exam_date']
        verbose_name = 'Экзамен'
        verbose_name_plural = 'Экзамены'
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('exam-detail', kwargs={'pk': self.pk})
    
    @property
    def total_topics(self):
        return self.topics.count()
    
    @property
    def completed_topics(self):
        return self.topics.filter(is_completed=True).count()
    
    @property
    def progress_percent(self):
        if self.total_topics == 0:
            return 0
        return int((self.completed_topics / self.total_topics) * 100)