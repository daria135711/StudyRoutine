from django.db import migrations, models


def convert_priority_to_text(apps, schema_editor):
    Topic = apps.get_model('topics', 'Topic')
    for topic in Topic.objects.all():
        value = topic.priority
        if value in ('высокий', 'средний', 'низкий'):
            continue
        try:
            num = int(value)
        except (TypeError, ValueError):
            num = 5
        if num >= 8:
            new_value = 'высокий'
        elif num >= 4:
            new_value = 'средний'
        else:
            new_value = 'низкий'
        topic.priority = new_value
        topic.save(update_fields=['priority'])


class Migration(migrations.Migration):

    dependencies = [
        ('topics', '0002_alter_topic_related_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='topic',
            name='priority',
            field=models.CharField(
                choices=[('высокий', 'Высокий'), ('средний', 'Средний'), ('низкий', 'Низкий')],
                default='средний',
                max_length=10,
            ),
        ),
        migrations.RunPython(convert_priority_to_text, migrations.RunPython.noop),
    ]
