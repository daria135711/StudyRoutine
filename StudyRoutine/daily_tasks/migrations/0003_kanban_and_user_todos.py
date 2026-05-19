import django.db.models.deletion
from django.db import migrations, models


def set_kanban_from_done(apps, schema_editor):
    DailyTask = apps.get_model('daily_tasks', 'DailyTask')
    for task in DailyTask.objects.all():
        task.kanban_status = 'done' if task.done else 'todo'
        task.save(update_fields=['kanban_status'])


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_user_password'),
        ('daily_tasks', '0002_dailytask_plan_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='dailytask',
            name='kanban_status',
            field=models.CharField(
                choices=[
                    ('todo', 'Нужно сделать'),
                    ('in_progress', 'В процессе'),
                    ('done', 'Завершено'),
                ],
                default='todo',
                max_length=16,
            ),
        ),
        migrations.RunPython(set_kanban_from_done, migrations.RunPython.noop),
        migrations.CreateModel(
            name='UserDailyTodo',
            fields=[
                ('id_todo', models.AutoField(primary_key=True, serialize=False)),
                ('date', models.DateField()),
                ('title', models.TextField()),
                ('description', models.TextField(blank=True, default='')),
                ('done', models.BooleanField(default=False)),
                (
                    'kanban_status',
                    models.CharField(
                        choices=[
                            ('todo', 'Нужно сделать'),
                            ('in_progress', 'В процессе'),
                            ('done', 'Завершено'),
                        ],
                        default='todo',
                        max_length=16,
                    ),
                ),
                (
                    'id_user',
                    models.ForeignKey(
                        db_column='id_user',
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='daily_todos',
                        to='users.user',
                    ),
                ),
            ],
            options={
                'verbose_name': 'User Daily Todo',
                'verbose_name_plural': 'User Daily Todos',
                'db_table': 'UserDailyTodo',
                'ordering': ['date', 'id_todo'],
            },
        ),
    ]
