import json
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Classroom
from apps.academics.models import (
    Exam,
    ExamQuestion,
    ExamSubjectWeight,
    Question,
    Subject,
)


User = get_user_model()


class Command(BaseCommand):
    help = "Local bazadagi tanlov asosida 2–11-sinflar uchun 20 savollik matematika testlarini yaratadi"

    @transaction.atomic
    def handle(self, *args, **options):
        data_path = (
            Path(__file__).resolve().parents[2]
            / "data"
            / "math_20_selection.json"
        )

        if not data_path.exists():
            raise CommandError(
                f"Tanlov fayli topilmadi: {data_path}"
            )

        payload = json.loads(data_path.read_text(encoding="utf-8"))

        expected_grades = {str(grade) for grade in range(2, 12)}
        received_grades = set(payload)

        if received_grades != expected_grades:
            raise CommandError(
                "JSON ichida aynan 2–11-sinflar bo‘lishi kerak. "
                f"Topildi: {sorted(received_grades)}"
            )

        admin = (
            User.objects.filter(role=User.Role.ADMIN).order_by("id").first()
            or User.objects.filter(is_superuser=True).order_by("id").first()
        )

        math = Subject.objects.filter(slug="math").first()

        if math is None:
            raise CommandError(
                "Matematika fani topilmadi. Avval asosiy matematika "
                "savollarini seed qiling."
            )

        created_count = 0
        updated_count = 0

        for grade in range(2, 12):
            spec = payload[str(grade)]
            question_specs = sorted(
                spec["questions"],
                key=lambda item: item["order"],
            )

            if len(question_specs) != 20:
                raise CommandError(
                    f"{grade}-sinf uchun 20 ta savol kutilgan edi, "
                    f"{len(question_specs)} ta topildi."
                )

            codes = [item["code"] for item in question_specs]
            questions_by_code = Question.objects.in_bulk(
                codes,
                field_name="code",
            )

            missing_codes = [
                code for code in codes
                if code not in questions_by_code
            ]

            if missing_codes:
                raise CommandError(
                    f"{grade}-sinf savollari topilmadi: "
                    f"{', '.join(missing_codes[:10])}. "
                    "Avval python manage.py seed_admission_2026 bajaring."
                )

            title = spec["title"]

            exam, created = Exam.objects.update_or_create(
                title=title,
                defaults={
                    "grade": grade,
                    "purpose": Exam.Purpose.ADMISSION,
                    "description": spec["description"],
                    "duration_minutes": spec["duration_minutes"],
                    "max_score": Decimal(spec["max_score"]),
                    "readiness_threshold": spec["readiness_threshold"],
                    "minimum_subject_score": spec["minimum_subject_score"],
                    "starts_at": timezone.now(),
                    "ends_at": timezone.now() + timedelta(days=3650),
                    "status": Exam.Status.ACTIVE,
                    "created_by": admin,
                },
            )

            created_count += int(created)
            updated_count += int(not created)

            exam.target_classrooms.set(
                Classroom.objects.filter(
                    grade=grade,
                    is_active=True,
                )
            )

            ExamSubjectWeight.objects.update_or_create(
                exam=exam,
                subject=math,
                defaults={
                    "weight_percent": Decimal("100.00"),
                    "max_score": Decimal("100.00"),
                },
            )

            exam.subject_weights.exclude(subject=math).delete()

            current_items = list(
                exam.exam_questions
                .select_related("question")
                .order_by("order", "id")
            )

            current_codes = [
                item.question.code
                for item in current_items
            ]

            has_answers = exam.exam_questions.filter(
                student_answers__isnull=False
            ).exists()

            if has_answers and current_codes != codes:
                raise CommandError(
                    f"{title} testida tarixiy javoblar mavjud. "
                    "Savollar tarkibini o‘zgartirib bo‘lmaydi."
                )

            if not has_answers:
                exam.exam_questions.exclude(
                    question__code__in=codes
                ).delete()

                for item in question_specs:
                    question = questions_by_code[item["code"]]

                    ExamQuestion.objects.update_or_create(
                        exam=exam,
                        question=question,
                        defaults={
                            "points": Decimal(item["points"]),
                            "order": item["order"],
                        },
                    )

            Exam.objects.filter(
                grade=grade,
                title=f"Qabul 2026 Matematika - {grade}-sinf",
            ).update(status=Exam.Status.ARCHIVED)

            Exam.objects.filter(
                grade=grade,
                title__startswith="RBIS Matematika Qabul Diagnostikasi",
            ).update(status=Exam.Status.ARCHIVED)

            self.stdout.write(
                self.style.SUCCESS(
                    f"{grade}-sinf: {title} — "
                    f"{exam.exam_questions.count()} savol"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                "20 savollik matematika testlari tayyor: "
                f"{created_count} ta yangi, "
                f"{updated_count} ta yangilangan."
            )
        )
