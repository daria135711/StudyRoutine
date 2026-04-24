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

    class Meta:
        db_table = 'DailyTask'
        verbose_name = 'Daily Task'
        verbose_name_plural = 'Daily Tasks'

    def __str__(self):
        return f"Task for User {self.id_user_id} on {self.date}"