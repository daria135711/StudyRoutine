from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('daily_tasks', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='dailytask',
            name='activity_type',
            field=models.CharField(blank=True, default='', max_length=32),
        ),
        migrations.AddField(
            model_name='dailytask',
            name='task_title',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='dailytask',
            name='task_description',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddConstraint(
            model_name='dailytask',
            constraint=models.UniqueConstraint(
                fields=('id_user', 'date', 'id_topic', 'activity_type'),
                name='unique_daily_task_slot',
            ),
        ),
    ]
