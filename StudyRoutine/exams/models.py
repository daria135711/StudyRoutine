from django.db import models
from users.models import User

class Exam(models.Model):
    id_exam = models.AutoField(primary_key=True)
    id_user = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        db_column='id_user',
        blank=True,
        null=True
    )
    title = models.TextField()
    date = models.DateField()
    difficulty = models.IntegerField()  

    class Meta:
        db_table = 'Exam'
        verbose_name = 'Exam'
        verbose_name_plural = 'Exams'

    def __str__(self):
        return self.title

class Topic(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Exam(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateField()
    #topics = models.ManyToManyField(Topic)

    def __str__(self):
        return self.name