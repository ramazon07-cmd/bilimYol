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
    QuestionOption,
    Skill,
    Subject,
    Topic,
)
from apps.diagnostics.english_placement_data import QUESTIONS, SKILL_SPECS, TOPIC_SPECS


User = get_user_model()


class Command(BaseCommand):
    help = "RBIS 5-11-sinflari uchun Test 3 asosidagi to‘liq 30 savollik English testlarini yaratadi"

    @transaction.atomic
    def handle(self, *args, **options):
        admin = (
            User.objects.filter(role=User.Role.ADMIN).order_by("id").first()
            or User.objects.filter(is_superuser=True).order_by("id").first()
        )
        subject, _ = Subject.objects.update_or_create(
            slug="english",
            defaults={
                "title": "English",
                "color": "#7A1233",
                "order": 2,
                "is_active": True,
            },
        )
        topics = self._upsert_topics(subject)
        skills = self._upsert_skills(subject)
        questions = [
            self._upsert_question(
                item=item,
                subject=subject,
                topic=topics[item["topic"]],
                skills=[skills[slug] for slug in item["skills"]],
                created_by=admin,
            )
            for item in QUESTIONS
        ]

        for grade in range(5, 12):
            exam = self._upsert_exam(
                grade=grade,
                subject=subject,
                questions=questions,
                created_by=admin,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"{grade}-sinf: {exam.title} - {exam.exam_questions.count()} savol, 50 daqiqa"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                "5-11-sinf English Test 3 tayyor: har bir sinf uchun to‘liq 30 savol."
            )
        )

    def _upsert_topics(self, subject):
        topics = {}
        for key, spec in TOPIC_SPECS.items():
            topic, _ = Topic.objects.update_or_create(
                subject=subject,
                code=spec["code"],
                defaults={
                    "title": spec["title"],
                    "description": "RBIS English placement diagnostikasi.",
                    "healthy_threshold": spec["healthy_threshold"],
                    "order": spec["order"],
                },
            )
            topics[key] = topic
        return topics

    def _upsert_skills(self, subject):
        skills = {}
        for slug, (title, order) in SKILL_SPECS.items():
            skill, _ = Skill.objects.update_or_create(
                subject=subject,
                slug=f"english-{slug}",
                defaults={
                    "title": title,
                    "description": "RBIS English placement diagnostik ko‘nikmasi.",
                    "order": order,
                },
            )
            skills[slug] = skill
        return skills

    def _upsert_question(self, *, item, subject, topic, skills, created_by):
        code = f"RBIS-ENG-PT3-{item['number']:02d}"
        desired_options = [
            {
                "label": chr(65 + index),
                "text": text,
                "is_correct": chr(65 + index) == item["answer"],
                "order": index,
            }
            for index, text in enumerate(item["options"])
        ]
        question = Question.objects.filter(code=code).first()
        if question is not None and question.exam_uses.filter(student_answers__isnull=False).exists():
            current_options = list(
                question.options.order_by("order", "id").values(
                    "label", "text", "is_correct", "order"
                )
            )
            unchanged = (
                question.subject_id == subject.id
                and question.topic_id == topic.id
                and question.context == item["context"]
                and question.prompt == item["prompt"]
                and question.explanation == item["explanation"]
                and question.difficulty == item["difficulty"]
                and current_options == desired_options
                and set(question.skills.values_list("id", flat=True)) == {skill.id for skill in skills}
            )
            if not unchanged:
                raise CommandError(
                    f"{code} savoliga javoblar mavjud va kontent o‘zgargan."
                )
            return question

        question, _ = Question.objects.update_or_create(
            code=code,
            defaults={
                "subject": subject,
                "topic": topic,
                "context": item["context"],
                "prompt": item["prompt"],
                "explanation": item["explanation"],
                "difficulty": item["difficulty"],
                "min_grade": 5,
                "max_grade": 11,
                "default_points": Decimal("1.00"),
                "is_active": True,
                "created_by": created_by,
            },
        )
        question.skills.set(skills)
        labels = []
        for option in desired_options:
            labels.append(option["label"])
            QuestionOption.objects.update_or_create(
                question=question,
                label=option["label"],
                defaults={
                    "text": option["text"],
                    "is_correct": option["is_correct"],
                    "order": option["order"],
                },
            )
        question.options.exclude(label__in=labels).delete()
        return question

    def _upsert_exam(self, *, grade, subject, questions, created_by):
        title = f"RBIS English Placement - {grade}-sinf"
        desired_ids = [question.id for question in questions]
        exam = Exam.objects.filter(title=title).order_by("id").first()

        if exam is not None:
            current_ids = list(
                exam.exam_questions.order_by("order", "id").values_list("question_id", flat=True)
            )
            has_answers = exam.exam_questions.filter(student_answers__isnull=False).exists()
            if has_answers and current_ids != desired_ids:
                legacy_title = f"{title} · Legacy {exam.id}"
                exam.title = legacy_title[:180]
                exam.status = Exam.Status.ARCHIVED
                exam.save(update_fields=["title", "status", "updated_at"])
                exam = None

        if exam is None:
            exam = Exam(title=title, starts_at=timezone.now())

        exam.grade = grade
        exam.purpose = Exam.Purpose.ADMISSION
        exam.description = (
            f"{grade}-sinf uchun Placement_Test_Grades_5-11 (2)(1).pdf "
            "asosidagi to‘liq 30 savollik English placement diagnostikasi."
        )
        exam.duration_minutes = 50
        exam.max_score = Decimal("100.00")
        exam.readiness_threshold = 60
        exam.minimum_subject_score = 50
        exam.ends_at = timezone.now() + timedelta(days=3650)
        exam.status = Exam.Status.ACTIVE
        if exam.created_by_id is None:
            exam.created_by = created_by
        exam.save()

        exam.target_classrooms.set(Classroom.objects.filter(grade=grade, is_active=True))
        exam.subject_weights.exclude(subject=subject).delete()
        ExamSubjectWeight.objects.update_or_create(
            exam=exam,
            subject=subject,
            defaults={
                "weight_percent": Decimal("100.00"),
                "max_score": Decimal("100.00"),
            },
        )

        has_answers = exam.exam_questions.filter(student_answers__isnull=False).exists()
        current_ids = list(
            exam.exam_questions.order_by("order", "id").values_list("question_id", flat=True)
        )
        if has_answers and current_ids != desired_ids:
            raise CommandError(f"{title}: tarixiy test tarkibini o‘zgartirib bo‘lmaydi.")
        if not has_answers:
            exam.exam_questions.exclude(question_id__in=desired_ids).delete()
            for order, question in enumerate(questions, 1):
                ExamQuestion.objects.update_or_create(
                    exam=exam,
                    question=question,
                    defaults={"points": Decimal("1.00"), "order": order},
                )
        return exam
