import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exams', '0001_initial'),
        ('study_plans', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExamPreparationPlan',
            fields=[
                ('id_plan_exam', models.AutoField(primary_key=True, serialize=False)),
                ('plan_data', models.JSONField()),
                ('generated_at', models.DateTimeField(auto_now=True)),
                (
                    'id_exam',
                    models.OneToOneField(
                        db_column='id_exam',
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='preparation_plan',
                        to='exams.exam',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Exam Preparation Plan',
                'verbose_name_plural': 'Exam Preparation Plans',
                'db_table': 'ExamPreparationPlan',
            },
        ),
    ]
