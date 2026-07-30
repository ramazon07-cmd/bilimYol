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
from apps.diagnostics.english_placement_data import (
    GRADE_LEVELS,
    GRADE_QUESTION_NUMBERS,
    QUESTIONS,
    SKILL_SPECS,
    TOPIC_SPECS,
    grade_bounds,
)


User = get_user_model()


class Command(BaseCommand):
    help = "RBIS 5-11-sinflari uchun English placement savollari va testlarini yaratadi"

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
                "color": "#65001F",
                "order": 2,
                "is_active": True,
            },
        )
        topics = self._upsert_topics(subject)
        skills = self._upsert_skills(subject)
        questions = {
            item["number"]: self._upsert_question(
                item=item,
                subject=subject,
                topic=topics[item["topic"]],
                skills=[skills[slug] for slug in item["skills"]],
                created_by=admin,
            )
            for item in QUESTIONS
        }

        created_exams = 0
        updated_exams = 0
        for grade in range(5, 12):
            exam, created = self._upsert_exam(
                grade=grade,
                subject=subject,
                questions=questions,
                created_by=admin,
            )
            created_exams += int(created)
            updated_exams += int(not created)
            self.stdout.write(
                self.style.SUCCESS(
                    f"{grade}-sinf: {exam.title} - "
                    f"{exam.exam_questions.count()} savol, target {GRADE_LEVELS[grade]}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                "English diagnostika tayyor: "
                f"30 ta savol, {created_exams} ta yangi va "
                f"{updated_exams} ta yangilangan grade testi."
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

        topic_order = [
            "grammar-foundations",
            "tense-and-voice",
            "advanced-syntax",
            "reading-narrative",
            "reading-culture",
            "critical-reading",
        ]
        for previous_key, current_key in zip(topic_order, topic_order[1:]):
            topics[current_key].prerequisites.add(topics[previous_key])
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

    def _upsert_question(self, item, subject, topic, skills, created_by):
        code = f"RBIS-ENG-PT3-{item['number']:02d}"
        min_grade, max_grade = grade_bounds(item["number"])
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
        if question is not None and self._question_has_answers(question):
            self._assert_used_question_unchanged(
                question=question,
                item=item,
                subject=subject,
                topic=topic,
                skills=skills,
                min_grade=min_grade,
                max_grade=max_grade,
                desired_options=desired_options,
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
                "min_grade": min_grade,
                "max_grade": max_grade,
                "default_points": Decimal("5.00"),
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

    def _question_has_answers(self, question):
        return question.exam_uses.filter(student_answers__isnull=False).exists()

    def _assert_used_question_unchanged(
        self,
        question,
        item,
        subject,
        topic,
        skills,
        min_grade,
        max_grade,
        desired_options,
    ):
        current_options = list(
            question.options.order_by("order", "id").values(
                "label", "text", "is_correct", "order"
            )
        )
        current_skill_ids = set(question.skills.values_list("id", flat=True))
        desired_skill_ids = {skill.id for skill in skills}
        unchanged = (
            question.subject_id == subject.id
            and question.topic_id == topic.id
            and question.context == item["context"]
            and question.prompt == item["prompt"]
            and question.explanation == item["explanation"]
            and question.difficulty == item["difficulty"]
            and question.min_grade == min_grade
            and question.max_grade == max_grade
            and question.default_points == Decimal("5.00")
            and current_skill_ids == desired_skill_ids
            and current_options == desired_options
        )
        if not unchanged:
            raise CommandError(
                f"{question.code} savoliga javoblar mavjud. Tarixiy natijani "
                "buzmaslik uchun savolni joyida o‘zgartirib bo‘lmaydi."
            )

    def _upsert_exam(self, grade, subject, questions, created_by):
        title = f"RBIS English Placement - {grade}-sinf"
        exam = Exam.objects.filter(title=title).first()
        created = exam is None
        if exam is None:
            exam = Exam(title=title, starts_at=timezone.now())

        exam.grade = grade
        exam.purpose = Exam.Purpose.ADMISSION
        exam.description = (
            f"{grade}-sinf uchun 20 savollik English placement diagnostikasi. "
            f"Maqsad daraja: {GRADE_LEVELS[grade]}. Savollar A1-C1 oralig‘ida "
            "bosqichma-bosqich tanlangan."
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

        matching_classrooms = Classroom.objects.filter(grade=grade, is_active=True)
        exam.target_classrooms.set(matching_classrooms)

        existing_weights = exam.subject_weights.exclude(subject=subject)
        if (
            existing_weights.exists()
            and exam.assignments.filter(attempts__isnull=False).exists()
        ):
            raise CommandError(
                f"{title} tarixiy urinishlarga ega va fan og‘irliklari o‘zgargan."
            )
        existing_weights.delete()
        ExamSubjectWeight.objects.update_or_create(
            exam=exam,
            subject=subject,
            defaults={
                "weight_percent": Decimal("100.00"),
                "max_score": Decimal("100.00"),
            },
        )

        desired_numbers = GRADE_QUESTION_NUMBERS[grade]
        desired_questions = [questions[number] for number in desired_numbers]
        desired_question_ids = [question.id for question in desired_questions]
        current_items = list(exam.exam_questions.order_by("order", "id"))
        current_question_ids = [item.question_id for item in current_items]
        has_answers = exam.exam_questions.filter(student_answers__isnull=False).exists()
        if has_answers and current_question_ids != desired_question_ids:
            raise CommandError(
                f"{title} testiga javoblar mavjud. Tarixiy test tarkibini "
                "joyida almashtirib bo‘lmaydi."
            )

        if not has_answers:
            exam.exam_questions.exclude(question_id__in=desired_question_ids).delete()
            for order, question in enumerate(desired_questions, 1):
                ExamQuestion.objects.update_or_create(
                    exam=exam,
                    question=question,
                    defaults={
                        "points": Decimal("5.00"),
                        "order": order,
                    },
                )
        return exam, created
