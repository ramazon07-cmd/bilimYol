from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("academics", "0004_exam_purpose_exam_recommended_categories_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="question",
            name="context",
            field=models.TextField(
                blank=True,
                help_text="Reading passage, scenario yoki savolga tegishli umumiy matn.",
            ),
        ),
    ]
