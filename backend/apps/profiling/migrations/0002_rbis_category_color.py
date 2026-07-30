from django.db import migrations, models


def normalize_default_category_color(apps, schema_editor):
    Category = apps.get_model("profiling", "Category")
    Category.objects.filter(color__iexact="#071b3a").update(color="#65001F")


class Migration(migrations.Migration):
    dependencies = [
        ("profiling", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="category",
            name="color",
            field=models.CharField(default="#65001F", max_length=20),
        ),
        migrations.RunPython(normalize_default_category_color, migrations.RunPython.noop),
    ]
