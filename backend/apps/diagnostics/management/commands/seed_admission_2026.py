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
    QuestionOption,
    Skill,
    Subject,
    Topic,
)

User = get_user_model()


def points_for(order: int) -> Decimal:
    return Decimal("3.34") if order <= 10 else Decimal("3.33")


class Command(BaseCommand):
    help = "Qabul test 2026 manbasidan matematika va English testlarini yaratadi"

    @transaction.atomic
    def handle(self, *args, **options):
        data_path = Path(__file__).resolve().parents[2] / "data" / "admission_2026.json"
        if not data_path.exists():
            raise CommandError(f"Test data fayli topilmadi: {data_path}")
        payload = json.loads(data_path.read_text(encoding="utf-8"))

        admin = (
            User.objects.filter(role=User.Role.ADMIN).order_by("id").first()
            or User.objects.filter(is_superuser=True).order_by("id").first()
        )
        math = self._subject("math", "Matematika", "#5F051F", 1)
        english = self._subject("english", "English", "#7A1233", 2)

        math_topic, _ = Topic.objects.update_or_create(
            subject=math,
            code="QABUL-2026-MATH",
            defaults={
                "title": "Qabul 2026 matematika",
                "description": "Qabul test 2026.zip hujjatlaridagi yozma matematika savollari.",
                "healthy_threshold": 60,
                "order": 1,
            },
        )
        math_skill, _ = Skill.objects.update_or_create(
            subject=math,
            slug="qabul-2026-written-solution",
            defaults={
                "title": "Yozma yechim",
                "description": "O‘quvchi javobni yozma yoki son ko‘rinishida kiritadi.",
                "order": 1,
            },
        )
        grammar_topic, _ = Topic.objects.update_or_create(
            subject=english,
            code="QABUL-2026-ENG-GRAMMAR",
            defaults={"title": "Grammar", "healthy_threshold": 60, "order": 1},
        )
        reading_topic, _ = Topic.objects.update_or_create(
            subject=english,
            code="QABUL-2026-ENG-READING",
            defaults={"title": "Reading", "healthy_threshold": 60, "order": 2},
        )
        grammar_skill, _ = Skill.objects.update_or_create(
            subject=english,
            slug="qabul-2026-grammar",
            defaults={"title": "Grammar accuracy", "order": 1},
        )
        reading_skill, _ = Skill.objects.update_or_create(
            subject=english,
            slug="qabul-2026-reading",
            defaults={"title": "Reading comprehension", "order": 2},
        )

        self._archive_old_seed_exams()

        math_question_sets = {}
        for source_key, rows in payload["math"].items():
            grade_bounds = {
                "g2": (2, 2), "g3": (3, 3), "g4": (4, 4), "g5": (5, 5),
                "g6": (6, 6), "g7": (7, 7), "g8-9": (8, 9), "g10-11": (10, 11),
            }[source_key]
            items = []
            for row in rows:
                code = f"Q26-MATH-{source_key.upper()}-{row['number']:02d}"
                question, _ = Question.objects.update_or_create(
                    code=code,
                    defaults={
                        "subject": math,
                        "topic": math_topic,
                        "context": "",
                        "prompt": row["prompt"] or f"Matematika savoli {row['number']}",
                        "explanation": "Manba hujjatda javob kaliti berilmagan; ustoz tekshiradi.",
                        "difficulty": Question.Difficulty.MEDIUM,
                        "min_grade": grade_bounds[0],
                        "max_grade": grade_bounds[1],
                        "default_points": points_for(row["number"]),
                        "image_url": row["image_url"],
                        "is_active": True,
                        "created_by": admin,
                    },
                )
                question.skills.set([math_skill])
                placeholder, _ = QuestionOption.objects.update_or_create(
                    question=question,
                    label="TEXT",
                    defaults={"text": "Yozma javob", "is_correct": False, "order": 0},
                )
                question.options.exclude(id=placeholder.id).delete()
                items.append(question)
            math_question_sets[source_key] = items

        english_question_sets = {}
        for test_key, test in payload["english"].items():
            items = []
            for row in test["questions"]:
                is_reading = row["number"] >= 16
                code = f"Q26-ENG-{test_key.upper()}-{row['number']:02d}"
                question, _ = Question.objects.update_or_create(
                    code=code,
                    defaults={
                        "subject": english,
                        "topic": reading_topic if is_reading else grammar_topic,
                        "context": row.get("context", ""),
                        "prompt": row["prompt"],
                        "explanation": "Qabul test 2026 answer key asosida baholanadi.",
                        "difficulty": (
                            Question.Difficulty.BASIC if row["number"] <= 10
                            else Question.Difficulty.MEDIUM if row["number"] <= 20
                            else Question.Difficulty.HIGH
                        ),
                        "min_grade": min(test["grades"]),
                        "max_grade": max(test["grades"]),
                        "default_points": points_for(row["number"]),
                        "image_url": "",
                        "is_active": True,
                        "created_by": admin,
                    },
                )
                question.skills.set([reading_skill if is_reading else grammar_skill])
                labels = []
                for index, text in enumerate(row["options"]):
                    label = chr(65 + index)
                    labels.append(label)
                    QuestionOption.objects.update_or_create(
                        question=question,
                        label=label,
                        defaults={
                            "text": text,
                            "is_correct": label == row["answer"],
                            "order": index,
                        },
                    )
                question.options.exclude(label__in=labels).delete()
                items.append(question)
            english_question_sets[test_key] = items

        exam_count = 0
        for grade in range(1, 12):
            test_key = "test1" if grade <= 2 else "test2" if grade <= 4 else "test3"
            test = payload["english"][test_key]
            self._upsert_exam(
                title=f"Qabul 2026 English - {grade}-sinf",
                grade=grade,
                subject=english,
                questions=english_question_sets[test_key],
                duration=test["duration_minutes"],
                description=(
                    f"Qabul test 2026 manbasidagi {test_key.upper()} — 30 savol. "
                    "Savollar original 1–30 tartibida."
                ),
                created_by=admin,
            )
            exam_count += 1

        math_grade_sources = {
            2: "g2", 3: "g3", 4: "g4", 5: "g5", 6: "g6", 7: "g7",
            8: "g8-9", 9: "g8-9", 10: "g10-11", 11: "g10-11",
        }
        for grade, source_key in math_grade_sources.items():
            self._upsert_exam(
                title=f"Qabul 2026 Matematika - {grade}-sinf",
                grade=grade,
                subject=math,
                questions=math_question_sets[source_key],
                duration=60,
                description=(
                    "Qabul test 2026 manbasidagi 30 ta yozma matematika savoli. "
                    "Manbada javob kaliti bo‘lmagani sababli ustoz tekshiradi."
                ),
                created_by=admin,
            )
            exam_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Qabul 2026 tayyor: 90 ta English, 240 ta matematika savoli; {exam_count} ta grade test."
        ))

    def _subject(self, slug, title, color, order):
        return Subject.objects.update_or_create(
            slug=slug,
            defaults={"title": title, "color": color, "order": order, "is_active": True},
        )[0]

    def _archive_old_seed_exams(self):
        Exam.objects.filter(title__startswith="RBIS English Placement").update(status=Exam.Status.ARCHIVED)
        Exam.objects.filter(title__startswith="RBIS Matematika Qabul Diagnostikasi").update(status=Exam.Status.ARCHIVED)

    def _upsert_exam(self, *, title, grade, subject, questions, duration, description, created_by):
        exam, _ = Exam.objects.update_or_create(
            title=title,
            defaults={
                "grade": grade,
                "purpose": Exam.Purpose.ADMISSION,
                "description": description,
                "duration_minutes": duration,
                "max_score": Decimal("100.00"),
                "readiness_threshold": 60,
                "minimum_subject_score": 50,
                "starts_at": timezone.now(),
                "ends_at": timezone.now() + timedelta(days=3650),
                "status": Exam.Status.ACTIVE,
                "created_by": created_by,
            },
        )
        exam.target_classrooms.set(Classroom.objects.filter(grade=grade, is_active=True))
        ExamSubjectWeight.objects.update_or_create(
            exam=exam,
            subject=subject,
            defaults={"weight_percent": Decimal("100.00"), "max_score": Decimal("100.00")},
        )
        exam.subject_weights.exclude(subject=subject).delete()

        desired = [q.id for q in questions]
        has_answers = exam.exam_questions.filter(student_answers__isnull=False).exists()
        current = list(exam.exam_questions.order_by("order", "id").values_list("question_id", flat=True))
        if has_answers and current != desired:
            raise CommandError(f"{title} testida tarixiy javoblar bor; tarkibni o‘zgartirib bo‘lmaydi.")
        if not has_answers:
            exam.exam_questions.exclude(question_id__in=desired).delete()
            for order, question in enumerate(questions, 1):
                ExamQuestion.objects.update_or_create(
                    exam=exam,
                    question=question,
                    defaults={"points": points_for(order), "order": order},
                )
        return exam
