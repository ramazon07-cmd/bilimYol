# Generated for bilimyol-sequential-diagnostic-batches-v6

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("diagnostics", "0004_examattempt_question_order"),
    ]

    operations = [
        migrations.AddField(
            model_name="examassignment",
            name="batch_id",
            field=models.UUIDField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="examassignment",
            name="batch_order",
            field=models.PositiveSmallIntegerField(default=1),
        ),
        migrations.AddField(
            model_name="examassignment",
            name="batch_size",
            field=models.PositiveSmallIntegerField(default=1),
        ),
    ]
