from django.db import migrations, models


def sync_certificate_status(apps, schema_editor):
    Certificate = apps.get_model("pathways", "Certificate")
    Certificate.objects.filter(is_verified=True).update(verification_status="verified")


class Migration(migrations.Migration):
    dependencies = [
        ("pathways", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="certificate",
            name="reviewed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="certificate",
            name="verification_note",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="certificate",
            name="verification_status",
            field=models.CharField(
                choices=[("pending", "Tekshiruvda"), ("verified", "Tasdiqlangan"), ("rejected", "Rad etilgan")],
                db_index=True,
                default="pending",
                max_length=16,
            ),
        ),
        migrations.RunPython(sync_certificate_status, migrations.RunPython.noop),
    ]
