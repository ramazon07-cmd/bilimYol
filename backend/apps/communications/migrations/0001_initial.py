import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Conversation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(choices=[("teacher", "O‘qituvchi"), ("academic", "Akademik bo‘lim")], max_length=16)),
                ("title", models.CharField(max_length=180)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_conversations", to=settings.AUTH_USER_MODEL)),
                ("parent", models.ForeignKey(limit_choices_to={"role": "parent"}, on_delete=django.db.models.deletion.CASCADE, related_name="parent_conversations", to=settings.AUTH_USER_MODEL)),
                ("student", models.ForeignKey(limit_choices_to={"role": "student"}, on_delete=django.db.models.deletion.CASCADE, related_name="student_conversations", to=settings.AUTH_USER_MODEL)),
                ("teacher", models.ForeignKey(blank=True, limit_choices_to={"role": "teacher"}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="teacher_conversations", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-updated_at"]},
        ),
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(choices=[("assignment", "Yangi test"), ("result", "Yangi natija"), ("roadmap", "Roadmap"), ("university", "Universitet maqsadi"), ("certificate", "Sertifikat"), ("message", "Xabar"), ("system", "Tizim")], db_index=True, default="system", max_length=24)),
                ("title", models.CharField(max_length=180)),
                ("message", models.TextField(blank=True)),
                ("action_path", models.CharField(blank=True, max_length=220)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("is_read", models.BooleanField(db_index=True, default=False)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("recipient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Message",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("body", models.TextField(max_length=3000)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("conversation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="communications.conversation")),
                ("sender", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sent_messages", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["created_at"]},
        ),
        migrations.AddConstraint(
            model_name="conversation",
            constraint=models.UniqueConstraint(fields=("student", "parent", "kind"), name="unique_family_conversation_kind"),
        ),
    ]
