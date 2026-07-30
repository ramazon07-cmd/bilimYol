from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from rest_framework.exceptions import ValidationError

from apps.accounts.models import Classroom
from apps.academics.models import Exam, Question
from apps.diagnostics.english_placement_data import GRADE_QUESTION_NUMBERS
from apps.diagnostics.models import ExamAssignment, StudentAnswer
from apps.diagnostics.services import start_attempt, subject_level, submit_attempt


User = get_user_model()


class EnglishDiagnosticSeedTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            username="english-admin",
            password="strong-admin-pass",
            full_name="English Admin",
            role=User.Role.ADMIN,
            is_staff=True,
        )
        cls.student = User.objects.create_user(
            username="english-student",
            password="strong-student-pass",
            full_name="English Student",
            role=User.Role.STUDENT,
        )
        for grade in range(5, 12):
            Classroom.objects.create(
                name=f"{grade}-English",
                grade=grade,
                program="RBIS English Placement",
                is_active=True,
            )
        call_command("seed_english_diagnostics", verbosity=0)

    def test_command_creates_30_tagged_questions_and_seven_grade_tests(self):
        questions = Question.objects.filter(code__startswith="RBIS-ENG-PT3-")
        self.assertEqual(questions.count(), 30)
        self.assertEqual(questions.filter(context__gt="").count(), 15)
        self.assertFalse(questions.filter(topic__isnull=True).exists())
        self.assertFalse(questions.filter(skills__isnull=True).exists())
        self.assertSetEqual(
            set(questions.values_list("difficulty", flat=True)),
            {"basic", "medium", "high"},
        )

        exams = Exam.objects.filter(title__startswith="RBIS English Placement - ")
        self.assertEqual(exams.count(), 7)
        for grade in range(5, 12):
            exam = exams.get(grade=grade)
            exam_questions = exam.exam_questions.select_related("question__subject")
            self.assertEqual(exam_questions.count(), 20)
            self.assertEqual(
                set(exam_questions.values_list("question__subject__slug", flat=True)),
                {"english"},
            )
            self.assertEqual(
                sum(item.points for item in exam_questions),
                Decimal("100.00"),
            )
            self.assertEqual(
                list(exam_questions.order_by("order").values_list("question__code", flat=True)),
                [
                    f"RBIS-ENG-PT3-{number:02d}"
                    for number in GRADE_QUESTION_NUMBERS[grade]
                ],
            )
            for item in exam_questions:
                self.assertLessEqual(item.question.min_grade, grade)
                self.assertGreaterEqual(item.question.max_grade, grade)
            weight = exam.subject_weights.get()
            self.assertEqual(weight.subject.slug, "english")
            self.assertEqual(weight.weight_percent, Decimal("100.00"))

    def test_command_is_idempotent(self):
        before = {
            "questions": Question.objects.filter(code__startswith="RBIS-ENG-PT3-").count(),
            "exams": Exam.objects.filter(title__startswith="RBIS English Placement - ").count(),
        }
        call_command("seed_english_diagnostics", verbosity=0)
        after = {
            "questions": Question.objects.filter(code__startswith="RBIS-ENG-PT3-").count(),
            "exams": Exam.objects.filter(title__startswith="RBIS English Placement - ").count(),
        }
        self.assertEqual(before, after)
        self.assertTrue(
            all(
                exam.exam_questions.count() == 20
                for exam in Exam.objects.filter(title__startswith="RBIS English Placement - ")
            )
        )

    @override_settings(DEBUG=False)
    def test_command_is_safe_to_run_outside_debug(self):
        call_command("seed_english_diagnostics", verbosity=0)
        self.assertEqual(
            Exam.objects.filter(title__startswith="RBIS English Placement - ").count(),
            7,
        )

    def test_question_order_is_randomized_once_and_persisted(self):
        exam = Exam.objects.get(title="RBIS English Placement - 8-sinf")
        assignment = ExamAssignment.objects.create(
            exam=exam,
            student=self.student,
            assigned_by=self.admin,
            is_active=True,
        )
        expected = list(
            exam.exam_questions.order_by("order", "id").values_list("id", flat=True)
        )
        with patch(
            "apps.diagnostics.services.SystemRandom.shuffle",
            side_effect=lambda values: values.reverse(),
        ):
            attempt = start_attempt(assignment, started_by=self.admin)
        self.assertEqual(attempt.question_order, list(reversed(expected)))
        self.assertEqual(
            start_attempt(assignment, started_by=self.admin).id,
            attempt.id,
        )

    def test_full_english_attempt_saves_answers_analysis_and_cefr(self):
        exam = Exam.objects.get(title="RBIS English Placement - 9-sinf")
        assignment = ExamAssignment.objects.create(
            exam=exam,
            student=self.student,
            assigned_by=self.admin,
            is_active=True,
        )
        attempt = start_attempt(assignment, started_by=self.admin)
        for exam_question in exam.exam_questions.select_related("question").all():
            StudentAnswer.objects.create(
                attempt=attempt,
                exam_question=exam_question,
                selected_option=exam_question.question.options.get(is_correct=True),
            )

        report = submit_attempt(attempt, submitted_by=self.admin)
        self.assertEqual(report.overall_score, Decimal("100.00"))
        self.assertEqual(report.subject_results.get().level, "C1")
        self.assertGreaterEqual(report.topic_results.count(), 3)
        self.assertGreaterEqual(report.skill_results.count(), 5)
        self.assertEqual(report.roadmap.stages.count(), 3)
        self.assertEqual(attempt.answers.count(), 20)

    def test_retake_requires_a_new_assignment(self):
        exam = Exam.objects.get(title="RBIS English Placement - 10-sinf")
        first_assignment = ExamAssignment.objects.create(
            exam=exam,
            student=self.student,
            assigned_by=self.admin,
            is_active=True,
        )
        first_attempt = start_attempt(first_assignment, started_by=self.admin)
        first_attempt.status = first_attempt.Status.SUBMITTED
        first_attempt.save(update_fields=["status"])
        with self.assertRaises(ValidationError):
            start_attempt(first_assignment, started_by=self.admin)

        first_assignment.is_active = False
        first_assignment.save(update_fields=["is_active"])
        retake_assignment = ExamAssignment.objects.create(
            exam=exam,
            student=self.student,
            assigned_by=self.admin,
            is_active=True,
        )
        retake_attempt = start_attempt(retake_assignment, started_by=self.admin)
        self.assertNotEqual(first_attempt.id, retake_attempt.id)

    def test_english_percentage_maps_to_cefr(self):
        expected = {
            Decimal("20"): "A1",
            Decimal("40"): "A2",
            Decimal("60"): "B1",
            Decimal("80"): "B2",
            Decimal("81"): "C1",
        }
        for score, level in expected.items():
            self.assertEqual(subject_level("english", score), level)
