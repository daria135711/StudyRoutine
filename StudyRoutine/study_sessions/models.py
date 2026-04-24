from django.db import models
from topics.models import Topic

class StudySession(models.Model):
    id_session = models.AutoField(primary_key=True)
    id_topic = models.ForeignKey(
        Topic,
        on_delete=models.DO_NOTHING,
        db_column='id_topic'
    )
    date = models.DateField()
    duration_minutes = models.IntegerField()
    completed = models.BooleanField()

    class Meta:
        db_table = 'StudySession'
        verbose_name = 'Study Session'
        verbose_name_plural = 'Study Sessions'

    def __str__(self):
        return f"Session on {self.date} - Topic {self.id_topic_id}"