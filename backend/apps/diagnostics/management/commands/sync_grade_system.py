from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import FieldDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.accounts.models import Classroom, ClassroomStudent
from apps.academics.models import Exam, ExamQuestion, ExamSubjectWeight
from apps.profiling.models import StudentProfile


User = get_user_model()


class Command(BaseCommand):
    help = "5–11 sinflar, testlar va student-classroom bog‘lanishini xavfsiz sinxronlaydi"

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
            raise CommandError("Savollari mavjud kamida bitta faol test topilmadi.")

        teacher = User.objects.filter(role=User.Role.TEACHER).order_by("id").first()
        admin = User.objects.filter(role=User.Role.ADMIN).order_by("id").first() or template.created_by

        enrolled_total = 0
        created_exam_total = 0

        for grade in range(5, 12):
            class_name = f"{grade}-A"
            classroom = Classroom.objects.filter(name=class_name).order_by("id").first()
            if classroom is None:
                classroom = Classroom.objects.create(
                    name=class_name,
                    grade=grade,
                    program="Prezident maktabiga tayyorgarlik",
                    teacher=teacher,
                    is_active=True,
                )
            else:
                classroom.grade = grade
                classroom.program = classroom.program or "Prezident maktabiga tayyorgarlik"
                classroom.teacher = classroom.teacher or teacher
                classroom.is_active = True
                classroom.save(update_fields=["grade", "program", "teacher", "is_active"])

            exam = Exam.objects.filter(
                grade=grade,
                status=Exam.Status.ACTIVE,
            ).order_by("id").first()

            if exam is None:
                defaults = {
                    "title": f"{grade}-sinf · IQ / Math / English Mock #1",
                    "grade": grade,
                    "description": f"{grade}-sinf uchun faol diagnostik test.",
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
                exam = Exam.objects.create(**defaults)
                created_exam_total += 1

            exam.target_classrooms.add(classroom)

            for weight in template.subject_weights.select_related("subject"):
                ExamSubjectWeight.objects.update_or_create(
                    exam=exam,
                    subject=weight.subject,
                    defaults={
                        "weight_percent": weight.weight_percent,
                        "max_score": weight.max_score,
                    },
                )

            for item in template.exam_questions.select_related("question"):
                ExamQuestion.objects.update_or_create(
                    exam=exam,
                    question=item.question,
                    defaults={"points": item.points, "order": item.order},
                )

            try:
                Exam._meta.get_field("recommended_categories")
            except FieldDoesNotExist:
                pass
            else:
                categories = list(template.recommended_categories.all())
                if categories and not exam.recommended_categories.exists():
                    exam.recommended_categories.set(categories)

            profiles = StudentProfile.objects.filter(grade=grade).select_related("student")
            for profile in profiles:
                ClassroomStudent.objects.filter(student=profile.student).exclude(
                    classroom__grade=grade,
                ).delete()
                _, created = ClassroomStudent.objects.get_or_create(
                    classroom=classroom,
                    student=profile.student,
                )
                enrolled_total += int(created)

            self.stdout.write(
                self.style.SUCCESS(
                    f"{grade}-sinf: {classroom.students.count()} o‘quvchi, test #{exam.id} tayyor"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Tayyor: {created_exam_total} yangi test, {enrolled_total} yangi sinf bog‘lanishi."
            )
        )
