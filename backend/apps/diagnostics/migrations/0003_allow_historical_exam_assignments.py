from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("diagnostics", "0002_examassignment_administered_by_and_more"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="examassignment",
            name="unique_exam_student_assignment",
        ),
        migrations.AddConstraint(
            model_name="examassignment",
            constraint=models.UniqueConstraint(
                fields=("exam", "student"),
                condition=models.Q(is_active=True),
                name="unique_active_exam_student_assignment",
            ),
        ),
    ]
