from django.db import models
from topics.models import Topic

class StudyPlan(models.Model):
    id_plan = models.AutoField(primary_key=True)
    id_topic = models.ForeignKey(
        Topic,
        on_delete=models.DO_NOTHING,
        db_column='id_topic'
    )
    planned_date = models.DateField()
    repetition_number = models.IntegerField()
    is_done = models.BooleanField(blank=True, null=True)

    class Meta:
        db_table = 'StudyPlan'
        verbose_name = 'Study Plan'
        verbose_name_plural = 'Study Plans'

    def __str__(self):
        return f"Plan for Topic {self.id_topic_id} on {self.planned_date}"