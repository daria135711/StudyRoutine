from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('topics', '0004_topicsubtopic'),
    ]

    operations = [
        migrations.AddField(
            model_name='topicsubtopic',
            name='generated_key',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='topicsubtopic',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='topicsubtopic',
            name='sort_order',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='topicsubtopic',
            name='source',
            field=models.CharField(
                choices=[('user', 'Пользователь'), ('generated', 'Сгенерировано')],
                default='user',
                max_length=16,
            ),
        ),
    ]
