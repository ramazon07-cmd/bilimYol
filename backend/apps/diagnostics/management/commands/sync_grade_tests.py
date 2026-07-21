from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import FieldDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.accounts.models import Classroom
from apps.academics.models import Exam, ExamQuestion, ExamSubjectWeight


User = get_user_model()


class Command(BaseCommand):
    help = "5–11-sinflar va ularga mos faol diagnostik testlarni xavfsiz yaratadi"

    def handle(self, *args, **options):
        template = (
            Exam.objects.filter(
                status=Exam.Status.ACTIVE,
                exam_questions__isnull=False,
            )
            .distinct()
            .order_by("grade", "id")
            .first()
        )

        if template is None:
            raise CommandError(
                "Kamida bitta savollari mavjud faol test kerak. Avval demo test yarating."
            )

        teacher = User.objects.filter(role=User.Role.TEACHER).order_by("id").first()
        admin = (
            User.objects.filter(role=User.Role.ADMIN).order_by("id").first()
            or template.created_by
        )

        created_classes = 0
        created_exams = 0
        updated_exams = 0

        for grade in range(5, 12):
            classroom, classroom_created = Classroom.objects.update_or_create(
                name=f"{grade}-A",
                defaults={
                    "grade": grade,
                    "program": "Prezident maktabiga tayyorgarlik",
                    "teacher": teacher,
                    "is_active": True,
                },
            )
            created_classes += int(classroom_created)

            existing = Exam.objects.filter(
                grade=grade,
                status=Exam.Status.ACTIVE,
            ).order_by("id").first()

            title = (
                existing.title
                if existing is not None
                else f"{grade}-sinf · IQ / Math / English Mock #1"
            )

            defaults = {
                "grade": grade,
                "description": (
                    f"{grade}-sinf uchun IQ, Matematika va English diagnostik testi."
                ),
                "duration_minutes": 75 if grade < 7 else 90,
                "max_score": template.max_score,
                "readiness_threshold": template.readiness_threshold,
                "minimum_subject_score": template.minimum_subject_score,
                "starts_at": timezone.now() - timedelta(minutes=5),
                "ends_at": timezone.now() + timedelta(days=365),
                "status": Exam.Status.ACTIVE,
                "created_by": admin,
            }

            try:
                Exam._meta.get_field("purpose")
            except FieldDoesNotExist:
                pass
            else:
                defaults["purpose"] = getattr(template, "purpose", "general")

            exam, exam_created = Exam.objects.update_or_create(
                title=title,
                defaults=defaults,
            )

            created_exams += int(exam_created)
            updated_exams += int(not exam_created)

            if hasattr(exam, "target_classrooms"):
                exam.target_classrooms.add(classroom)

            for weight in template.subject_weights.select_related("subject").all():
                ExamSubjectWeight.objects.update_or_create(
                    exam=exam,
                    subject=weight.subject,
                    defaults={
                        "weight_percent": weight.weight_percent,
                        "max_score": weight.max_score,
                    },
                )

            for item in template.exam_questions.select_related("question").all():
                ExamQuestion.objects.update_or_create(
                    exam=exam,
                    question=item.question,
                    defaults={
                        "points": item.points,
                        "order": item.order,
                    },
                )

            if hasattr(exam, "recommended_categories"):
                template_categories = list(template.recommended_categories.all())
                if template_categories:
                    exam.recommended_categories.set(template_categories)

            self.stdout.write(
                self.style.SUCCESS(
                    f"{grade}-sinf: {classroom.name} va {exam.title} tayyor"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Sinxronlash tugadi: "
                f"{created_classes} yangi sinf, "
                f"{created_exams} yangi test, "
                f"{updated_exams} yangilangan test."
            )
        )
