from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("diagnostics", "0003_allow_historical_exam_assignments"),
    ]

    operations = [
        migrations.AddField(
            model_name="examattempt",
            name="question_order",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="Urinish boshlanganda saqlangan ExamQuestion ID tartibi.",
            ),
        ),
    ]
