from datetime import timedelta
from decimal import Decimal

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


GRADE_SOURCES = {
    2: "G2",
    3: "G3",
    4: "G4",
    5: "G5",
    6: "G6",
    7: "G7",
    8: "G8-9",
    9: "G8-9",
    10: "G10-11",
    11: "G10-11",
}


class Command(BaseCommand):
    help = (
        "Javob kaliti mavjud savollardan "
        "20 savollik matematika testlarini yaratadi"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--grade",
            type=int,
            choices=range(2, 12),
            help="Faqat bitta sinf uchun yaratish",
        )
        parser.add_argument(
            "--duration",
            type=int,
            default=40,
            help="Test davomiyligi, daqiqada. Default: 40",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        duration = options["duration"]
        selected_grade = options.get("grade")

        if duration < 10:
            raise CommandError(
                "Test davomiyligi kamida 10 daqiqa bo‘lishi kerak."
            )

        math = Subject.objects.get(slug="math")

        admin = (
            User.objects.filter(role=User.Role.ADMIN)
            .order_by("id")
            .first()
            or User.objects.filter(is_superuser=True)
            .order_by("id")
            .first()
        )

        grades = (
            [selected_grade]
            if selected_grade
            else list(GRADE_SOURCES.keys())
        )

        created_count = 0
        skipped_count = 0

        for grade in grades:
            source = GRADE_SOURCES[grade]
            prefix = f"Q26-MATH-{source}-"

            all_questions = list(
                Question.objects.filter(
                    subject=math,
                    code__startswith=prefix,
                    is_active=True,
                ).order_by("code")
            )

            answered_questions = [
                question
                for question in all_questions
                if question.accepted_text_answers.strip()
            ]

            if len(answered_questions) < 20:
                missing = 20 - len(answered_questions)

                self.stdout.write(
                    self.style.WARNING(
                        f"{grade}-sinf: SKIP — "
                        f"{len(answered_questions)}/20 tayyor. "
                        f"Yana {missing} ta javob kaliti kerak."
                    )
                )

                skipped_count += 1
                continue

            # Original tartibdagi dastlabki 20 ta
            selected_questions = answered_questions[:20]

            new_title = (
                f"Qabul 2026 Matematika - "
                f"{grade}-sinf (20 savol)"
            )

            old_title = (
                f"Qabul 2026 Matematika - "
                f"{grade}-sinf"
            )

            old_exam = Exam.objects.filter(
                title=old_title
            ).first()

            if (
                old_exam
                and old_exam.assignments.filter(
                    is_active=True
                ).exists()
            ):
                self.stdout.write(
                    self.style.WARNING(
                        f"{grade}-sinf: eski testda faol "
                        "assignment mavjud. Avval uni yakunlang."
                    )
                )
                skipped_count += 1
                continue

            exam, created = Exam.objects.update_or_create(
                title=new_title,
                defaults={
                    "grade": grade,
                    "purpose": Exam.Purpose.ADMISSION,
                    "description": (
                        "Qabul 2026 matematika savollar "
                        "bankidan javob kaliti mavjud "
                        "20 ta savol."
                    ),
                    "duration_minutes": duration,
                    "max_score": Decimal("100.00"),
                    "readiness_threshold": 60,
                    "minimum_subject_score": 50,
                    "starts_at": timezone.now(),
                    "ends_at": (
                        timezone.now()
                        + timedelta(days=3650)
                    ),
                    "status": Exam.Status.ACTIVE,
                    "created_by": admin,
                },
            )

            # Yangi test ishlatilgan bo‘lsa tarkibini
            # keyinchalik o‘zgartirmaymiz.
            has_history = exam.exam_questions.filter(
                student_answers__isnull=False
            ).exists()

            selected_ids = [
                question.id
                for question in selected_questions
            ]

            current_ids = list(
                exam.exam_questions.order_by(
                    "order",
                    "id",
                ).values_list(
                    "question_id",
                    flat=True,
                )
            )

            if has_history and current_ids != selected_ids:
                self.stdout.write(
                    self.style.WARNING(
                        f"{grade}-sinf: yangi testda tarixiy "
                        "javoblar mavjud. Tarkib o‘zgartirilmadi."
                    )
                )
                skipped_count += 1
                continue

            if not has_history:
                exam.exam_questions.exclude(
                    question_id__in=selected_ids
                ).delete()

                for order, question in enumerate(
                    selected_questions,
                    start=1,
                ):
                    ExamQuestion.objects.update_or_create(
                        exam=exam,
                        question=question,
                        defaults={
                            "points": Decimal("5.00"),
                            "order": order,
                        },
                    )

            ExamSubjectWeight.objects.update_or_create(
                exam=exam,
                subject=math,
                defaults={
                    "weight_percent": Decimal("100.00"),
                    "max_score": Decimal("100.00"),
                },
            )

            exam.subject_weights.exclude(
                subject=math
            ).delete()

            exam.target_classrooms.set(
                Classroom.objects.filter(
                    grade=grade,
                    is_active=True,
                )
            )

            if old_exam:
                old_exam.status = Exam.Status.ARCHIVED
                old_exam.save(update_fields=["status"])

            created_count += 1

            codes = ", ".join(
                question.code
                for question in selected_questions
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"{grade}-sinf: 20 savol, "
                    f"{duration} daqiqa, 5 ball/savol."
                )
            )
            self.stdout.write(f"  {codes}")

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Yaratildi/yangilandi: {created_count}; "
                f"o‘tkazib yuborildi: {skipped_count}."
            )
        )