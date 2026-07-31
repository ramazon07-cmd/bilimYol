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
from apps.diagnostics.math_placement_data import (
    DURATION_MINUTES,
    QUESTIONS_BY_GRADE,
    SKILL_SPECS,
    TOPIC_SPECS,
)


User = get_user_model()


def points_for(grade: int, order: int) -> Decimal:
    """Distribute exactly 100 points over each grade test."""
    question_count = len(QUESTIONS_BY_GRADE[grade])
    if question_count == 20:
        return Decimal("5.00")
    # 10 × 3.34 + 20 × 3.33 = 100.00
    return Decimal("3.34") if order <= 10 else Decimal("3.33")


class Command(BaseCommand):
    help = "RBIS 2-4-sinflari uchun matematika qabul diagnostikasini yaratadi"

    @transaction.atomic
    def handle(self, *args, **options):
        admin = (
            User.objects.filter(role=User.Role.ADMIN).order_by("id").first()
            or User.objects.filter(is_superuser=True).order_by("id").first()
        )
        subject, _ = Subject.objects.update_or_create(
            slug="math",
            defaults={
                "title": "Matematika",
                "color": "#5F051F",
                "order": 1,
                "is_active": True,
            },
        )
        topics = self._upsert_topics(subject)
        skills = self._upsert_skills(subject)

        created_exams = 0
        updated_exams = 0
        total_questions = 0
        for grade, items in QUESTIONS_BY_GRADE.items():
            questions = []
            for order, item in enumerate(items, 1):
                questions.append(
                    self._upsert_question(
                        grade=grade,
                        order=order,
                        item=item,
                        subject=subject,
                        topic=topics[item["topic"]],
                        skills=[skills[slug] for slug in item["skills"]],
                        created_by=admin,
                    )
                )
            exam, created = self._upsert_exam(
                grade=grade,
                subject=subject,
                questions=questions,
                created_by=admin,
            )
            created_exams += int(created)
            updated_exams += int(not created)
            total_questions += len(questions)
            self.stdout.write(
                self.style.SUCCESS(
                    f"{grade}-sinf: {exam.title} — {len(questions)} savol, 100 ball"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Matematika diagnostikasi tayyor: "
                f"{total_questions} ta savol, {created_exams} ta yangi va "
                f"{updated_exams} ta yangilangan test."
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
                    "description": "RBIS boshlang‘ich matematika qabul diagnostikasi.",
                    "healthy_threshold": spec["healthy_threshold"],
                    "order": spec["order"],
                },
            )
            topics[key] = topic

        topic_order = [
            "numbers",
            "word-problems",
            "algebra",
            "patterns",
            "geometry",
            "measurement",
            "data",
            "logic",
        ]
        for previous_key, current_key in zip(topic_order, topic_order[1:]):
            topics[current_key].prerequisites.add(topics[previous_key])
        return topics

    def _upsert_skills(self, subject):
        skills = {}
        for slug, (title, order) in SKILL_SPECS.items():
            skill, _ = Skill.objects.update_or_create(
                subject=subject,
                slug=f"math-{slug}",
                defaults={
                    "title": title,
                    "description": "RBIS boshlang‘ich matematika diagnostik ko‘nikmasi.",
                    "order": order,
                },
            )
            skills[slug] = skill
        return skills

    def _upsert_question(self, grade, order, item, subject, topic, skills, created_by):
        code = f"RBIS-MATH-G{grade}-{item['number']:02d}"
        points = points_for(grade, order)
        image_url = (
            f"/question-assets/math/{item['image']}" if item.get("image") else ""
        )
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
                grade=grade,
                points=points,
                image_url=image_url,
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
                "min_grade": grade,
                "max_grade": grade,
                "default_points": points,
                "image_url": image_url,
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
        grade,
        points,
        image_url,
        desired_options,
    ):
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
            and question.min_grade == grade
            and question.max_grade == grade
            and question.default_points == points
            and question.image_url == image_url
            and set(question.skills.values_list("id", flat=True))
            == {skill.id for skill in skills}
            and current_options == desired_options
        )
        if not unchanged:
            raise CommandError(
                f"{question.code} savoliga javoblar mavjud. Tarixiy natijani "
                "buzmaslik uchun savolni joyida o‘zgartirib bo‘lmaydi."
            )

    def _upsert_exam(self, grade, subject, questions, created_by):
        title = f"RBIS Matematika Qabul Diagnostikasi - {grade}-sinf"
        exam = Exam.objects.filter(title=title).first()
        created = exam is None
        if exam is None:
            exam = Exam(title=title, starts_at=timezone.now())

        question_count = len(questions)
        exam.grade = grade
        exam.purpose = Exam.Purpose.ADMISSION
        exam.description = (
            f"{grade}-sinfga yangi o‘tgan o‘quvchilar uchun {question_count} "
            "savollik matematika qabul diagnostikasi. Natija 100 ballik "
            "shkalaga normallashtiriladi."
        )
        exam.duration_minutes = DURATION_MINUTES[grade]
        exam.max_score = Decimal("100.00")
        exam.readiness_threshold = 60
        exam.minimum_subject_score = 50
        exam.ends_at = timezone.now() + timedelta(days=3650)
        exam.status = Exam.Status.ACTIVE
        if exam.created_by_id is None:
            exam.created_by = created_by
        exam.save()

        exam.target_classrooms.set(
            Classroom.objects.filter(grade=grade, is_active=True)
        )

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
                        "points": points_for(grade, order),
                        "order": order,
                    },
                )
        return exam, created
