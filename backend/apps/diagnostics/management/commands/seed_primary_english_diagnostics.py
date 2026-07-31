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
from apps.diagnostics.english_placement_data import SKILL_SPECS, TOPIC_SPECS
from apps.diagnostics.english_primary_placement_data import PRIMARY_TESTS


User = get_user_model()


class Command(BaseCommand):
    help = "RBIS 1-4-sinflari uchun 30 savollik English placement testlarini yaratadi"

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

        created_exams = 0
        updated_exams = 0
        created_questions = 0
        updated_questions = 0

        for test_code, spec in PRIMARY_TESTS.items():
            question_map = {}
            min_grade = min(spec["grades"])
            max_grade = max(spec["grades"])
            for item in spec["questions"]:
                question, created = self._upsert_question(
                    test_code=test_code,
                    item=item,
                    subject=subject,
                    topic=topics[item["topic"]],
                    skills=[skills[slug] for slug in item["skills"]],
                    created_by=admin,
                    min_grade=min_grade,
                    max_grade=max_grade,
                )
                question_map[item["number"]] = question
                created_questions += int(created)
                updated_questions += int(not created)

            for grade in spec["grades"]:
                exam, created = self._upsert_exam(
                    grade=grade,
                    spec=spec,
                    subject=subject,
                    questions=[question_map[number] for number in range(1, 31)],
                    created_by=admin,
                )
                created_exams += int(created)
                updated_exams += int(not created)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"{grade}-sinf: {exam.title} - "
                        f"{exam.exam_questions.count()} savol, {exam.duration_minutes} daqiqa"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                "Primary English diagnostika tayyor: "
                f"{created_questions} yangi / {updated_questions} yangilangan savol; "
                f"{created_exams} yangi / {updated_exams} yangilangan test."
            )
        )

    def _upsert_topics(self, subject):
        topics = {}
        required = {"grammar-foundations", "tense-and-voice", "reading-narrative"}
        for key in required:
            spec = TOPIC_SPECS[key]
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

        topics["tense-and-voice"].prerequisites.add(topics["grammar-foundations"])
        topics["reading-narrative"].prerequisites.add(topics["grammar-foundations"])
        return topics

    def _upsert_skills(self, subject):
        required = {
            "grammar-accuracy",
            "question-formation",
            "tense-control",
            "factual-reading",
        }
        skills = {}
        for slug in required:
            title, order = SKILL_SPECS[slug]
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

    def _upsert_question(
        self,
        *,
        test_code,
        item,
        subject,
        topic,
        skills,
        created_by,
        min_grade,
        max_grade,
    ):
        code = f"RBIS-ENG-{test_code}-{item['number']:02d}"
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
            return question, False

        question, created = Question.objects.update_or_create(
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
        return question, created

    def _question_has_answers(self, question):
        return question.exam_uses.filter(student_answers__isnull=False).exists()

    def _assert_used_question_unchanged(
        self,
        *,
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
            and question.default_points == Decimal("1.00")
            and current_skill_ids == desired_skill_ids
            and current_options == desired_options
        )
        if not unchanged:
            raise CommandError(
                f"{question.code} savoliga javoblar mavjud. Tarixiy natijani "
                "buzmaslik uchun savolni joyida o‘zgartirib bo‘lmaydi."
            )

    def _upsert_exam(self, *, grade, spec, subject, questions, created_by):
        title = f"RBIS English Placement - {grade}-sinf"
        exam = Exam.objects.filter(title=title).first()
        created = exam is None
        if exam is None:
            exam = Exam(title=title, starts_at=timezone.now())

        exam.grade = grade
        exam.purpose = Exam.Purpose.ADMISSION
        exam.description = (
            f"{grade}-sinf uchun 30 savollik English placement diagnostikasi. "
            f"Manba: {spec['source_name']}. Daraja diapazoni: {spec['level_range']}."
        )
        exam.duration_minutes = spec["duration_minutes"]
        exam.max_score = Decimal("100.00")
        exam.readiness_threshold = 60
        exam.minimum_subject_score = 50
        exam.ends_at = timezone.now() + timedelta(days=3650)
        exam.status = Exam.Status.ACTIVE
        if exam.created_by_id is None:
            exam.created_by = created_by
        exam.save()

        exam.target_classrooms.set(Classroom.objects.filter(grade=grade, is_active=True))

        other_weights = exam.subject_weights.exclude(subject=subject)
        if other_weights.exists() and exam.assignments.filter(attempts__isnull=False).exists():
            raise CommandError(
                f"{title} tarixiy urinishlarga ega va fan og‘irliklari o‘zgargan."
            )
        other_weights.delete()
        ExamSubjectWeight.objects.update_or_create(
            exam=exam,
            subject=subject,
            defaults={
                "weight_percent": Decimal("100.00"),
                "max_score": Decimal("100.00"),
            },
        )

        desired_question_ids = [question.id for question in questions]
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
            for order, question in enumerate(questions, 1):
                ExamQuestion.objects.update_or_create(
                    exam=exam,
                    question=question,
                    defaults={
                        "points": Decimal("1.00"),
                        "order": order,
                    },
                )
        return exam, created
