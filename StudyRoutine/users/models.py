from django.db import models

class User(models.Model):
    id_user = models.AutoField(primary_key=True)
    username = models.TextField(blank=True, null=True)
    email = models.TextField(blank=True, null=True)
    password = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'User'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.username or f"User {self.id_user}"