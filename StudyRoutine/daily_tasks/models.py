from django.db import models
from users.models import User
from topics.models import Topic

class DailyTask(models.Model):
    id_daily = models.AutoField(primary_key=True)
    id_user = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        db_column='id_user'
    )
    date = models.DateField()
    id_topic = models.ForeignKey(
        Topic,
        on_delete=models.DO_NOTHING,
        db_column='id_topic'
    )
    done = models.BooleanField()
    activity_type = models.CharField(max_length=32, blank=True, default='')
    task_title = models.TextField(blank=True, default='')
    task_description = models.TextField(blank=True, default='')

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

    def __str__(self):
        return f"Task for User {self.id_user_id} on {self.date}"