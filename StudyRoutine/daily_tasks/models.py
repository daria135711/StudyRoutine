from django.db import models

from topics.models import Topic
from users.models import User

KANBAN_TODO = 'todo'
KANBAN_IN_PROGRESS = 'in_progress'
KANBAN_DONE = 'done'

KANBAN_CHOICES = (
    (KANBAN_TODO, 'Нужно сделать'),
    (KANBAN_IN_PROGRESS, 'В процессе'),
    (KANBAN_DONE, 'Завершено'),
)


class DailyTask(models.Model):
    id_daily = models.AutoField(primary_key=True)
    id_user = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        db_column='id_user',
    )
    date = models.DateField()
    id_topic = models.ForeignKey(
        Topic,
        on_delete=models.DO_NOTHING,
        db_column='id_topic',
    )
    done = models.BooleanField()
    activity_type = models.CharField(max_length=32, blank=True, default='')
    task_title = models.TextField(blank=True, default='')
    task_description = models.TextField(blank=True, default='')
    kanban_status = models.CharField(
        max_length=16,
        choices=KANBAN_CHOICES,
        default=KANBAN_TODO,
    )

    class Meta:
        db_table = 'DailyTask'
        verbose_name = 'Daily Task'
        verbose_name_plural = 'Daily Tasks'
        constraints = [
            models.UniqueConstraint(
                fields=['id_user', 'date', 'id_topic', 'activity_type'],
                name='unique_daily_task_slot',
            ),
        ]

    ACTIVITY_LABELS = {
        'theory': 'Теория',
        'practice_basic': 'Базовая практика',
        'theory_advanced': 'Углублённая теория',
        'practice_exam': 'Экзаменационная практика',
    }

    @property
    def activity_label(self):
        return self.ACTIVITY_LABELS.get(self.activity_type, '')

    def display_title(self):
        return self.task_title or self.id_topic.title

    def apply_kanban_status(self, status: str):
        self.kanban_status = status
        self.done = status == KANBAN_DONE

    def __str__(self):
        return f"Task for User {self.id_user_id} on {self.date}"


class UserDailyTodo(models.Model):
    id_todo = models.AutoField(primary_key=True)
    id_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column='id_user',
        related_name='daily_todos',
    )
    date = models.DateField()
    title = models.TextField()
    description = models.TextField(blank=True, default='')
    done = models.BooleanField(default=False)
    kanban_status = models.CharField(
        max_length=16,
        choices=KANBAN_CHOICES,
        default=KANBAN_TODO,
    )

    class Meta:
        db_table = 'UserDailyTodo'
        verbose_name = 'User Daily Todo'
        verbose_name_plural = 'User Daily Todos'
        ordering = ['date', 'id_todo']

    def apply_kanban_status(self, status: str):
        self.kanban_status = status
        self.done = status == KANBAN_DONE

    def __str__(self):
        return self.title
