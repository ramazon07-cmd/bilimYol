from django.db import migrations, models


def apply_rbis_subject_colors(apps, schema_editor):
    Subject = apps.get_model("academics", "Subject")
    colors = {
        "math": "#65001F",
        "english": "#7A1233",
        "iq": "#450417",
    }
    for slug, color in colors.items():
        Subject.objects.filter(slug=slug).update(color=color)


class Migration(migrations.Migration):
    dependencies = [
        ("academics", "0005_question_context"),
    ]

    operations = [
        migrations.AlterField(
            model_name="subject",
            name="color",
            field=models.CharField(default="#65001F", max_length=20),
        ),
        migrations.RunPython(apply_rbis_subject_colors, migrations.RunPython.noop),
    ]
