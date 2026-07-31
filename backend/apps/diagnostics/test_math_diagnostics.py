from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.academics.models import (
    Exam,
    ExamQuestion,
    ExamSubjectWeight,
    Question,
    Subject,
)
from apps.academics.policies import is_enabled_diagnostic_exam
from apps.diagnostics.models import ExamAssignment
from apps.profiling.models import StudentProfile


User = get_user_model()


@override_settings(
    DEBUG=True,
    DIAGNOSTIC_ACTIVE_SUBJECTS=("english", "math"),
)
class MathPlacementDiagnosticsTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", verbosity=0)
        call_command("seed_math_diagnostics", verbosity=0)

    def test_grade_tests_have_expected_question_counts_and_exact_100_points(self):
        expected_counts = {2: 20, 3: 30, 4: 30}
        for grade, expected_count in expected_counts.items():
            exam = Exam.objects.get(
                title=f"RBIS Matematika Qabul Diagnostikasi - {grade}-sinf"
            )
            self.assertTrue(is_enabled_diagnostic_exam(exam))
            self.assertEqual(exam.exam_questions.count(), expected_count)
            self.assertEqual(
                sum(
                    exam.exam_questions.values_list("points", flat=True),
                    Decimal("0.00"),
                ),
                Decimal("100.00"),
            )
            self.assertSetEqual(
                set(
                    exam.exam_questions.values_list(
                        "question__subject__slug", flat=True
                    )
                ),
                {"math"},
            )

    def test_every_math_question_has_one_correct_option(self):
        questions = Question.objects.filter(code__startswith="RBIS-MATH-G")
        self.assertEqual(questions.count(), 80)
        for question in questions:
            self.assertEqual(question.options.filter(is_correct=True).count(), 1)
            self.assertGreaterEqual(question.options.count(), 4)

    def test_visual_questions_have_frontend_asset_paths(self):
        visual_questions = Question.objects.filter(
            code__startswith="RBIS-MATH-G"
        ).exclude(image_url="")
        self.assertEqual(visual_questions.count(), 28)
        self.assertTrue(
            all(
                path.startswith("/question-assets/math/")
                for path in visual_questions.values_list("image_url", flat=True)
            )
        )

    def test_seed_is_idempotent(self):
        before = {
            "questions": Question.objects.filter(code__startswith="RBIS-MATH-G").count(),
            "exams": Exam.objects.filter(
                title__startswith="RBIS Matematika Qabul Diagnostikasi"
            ).count(),
        }
        call_command("seed_math_diagnostics", verbosity=0)
        after = {
            "questions": Question.objects.filter(code__startswith="RBIS-MATH-G").count(),
            "exams": Exam.objects.filter(
                title__startswith="RBIS Matematika Qabul Diagnostikasi"
            ).count(),
        }
        self.assertEqual(before, after)

    def test_student_can_complete_grade_2_math_exam_and_review_every_answer(self):
        student = User.objects.create_user(
            username="grade-2-math-student",
            password="strong-pass-123",
            full_name="2-sinf matematika o‘quvchisi",
            role=User.Role.STUDENT,
        )
        exam = Exam.objects.get(
            title="RBIS Matematika Qabul Diagnostikasi - 2-sinf"
        )
        assignment = ExamAssignment.objects.create(
            exam=exam,
            student=student,
            assigned_by=User.objects.get(username="admin"),
            is_active=True,
        )

        self.client.force_authenticate(student)
        started = self.client.post(
            f"/api/assignments/{assignment.id}/start/", {}, format="json"
        )
        self.assertEqual(started.status_code, 201)
        attempt_id = started.data["id"]

        for exam_question in exam.exam_questions.select_related("question"):
            correct_option = exam_question.question.options.get(is_correct=True)
            answered = self.client.post(
                f"/api/attempts/{attempt_id}/answer/",
                {
                    "exam_question": exam_question.id,
                    "selected_option": correct_option.id,
                    "is_flagged": False,
                },
                format="json",
            )
            self.assertEqual(answered.status_code, 200)

        submitted = self.client.post(
            f"/api/attempts/{attempt_id}/submit/", {}, format="json"
        )
        self.assertEqual(submitted.status_code, 200)
        self.assertEqual(float(submitted.data["overall_score"]), 100.0)
        self.assertEqual(
            submitted.data["subject_results"][0]["subject"]["slug"], "math"
        )

        detail = self.client.get(f"/api/reports/{submitted.data['id']}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(len(detail.data["question_review"]), 20)
        self.assertTrue(all(row["is_correct"] for row in detail.data["question_review"]))
        self.assertTrue(all(row["correct_option"] for row in detail.data["question_review"]))
        self.assertTrue(all(row["selected_option"] for row in detail.data["question_review"]))

    def _create_grade_2_english_exam(self):
        existing = Exam.objects.filter(title="RBIS English Placement - 2-sinf").first()
        if existing:
            return existing

        admin = User.objects.get(username="admin")
        english = Subject.objects.get(slug="english")
        question = Question.objects.filter(subject=english).first()
        self.assertIsNotNone(question)
        exam = Exam.objects.create(
            title="RBIS English Placement - 2-sinf",
            grade=2,
            purpose=Exam.Purpose.ADMISSION,
            description="2-sinf uchun English diagnostikasi.",
            duration_minutes=30,
            max_score=Decimal("100.00"),
            readiness_threshold=60,
            minimum_subject_score=50,
            starts_at=timezone.now(),
            ends_at=timezone.now() + timedelta(days=365),
            status=Exam.Status.ACTIVE,
            created_by=admin,
        )
        ExamSubjectWeight.objects.create(
            exam=exam,
            subject=english,
            weight_percent=Decimal("100.00"),
            max_score=Decimal("100.00"),
        )
        ExamQuestion.objects.create(
            exam=exam,
            question=question,
            points=Decimal("100.00"),
            order=1,
        )
        return exam

    def test_grade_match_recommends_and_assigns_both_math_and_english(self):
        english_exam = self._create_grade_2_english_exam()
        math_exam = Exam.objects.get(
            title="RBIS Matematika Qabul Diagnostikasi - 2-sinf"
        )
        admin = User.objects.get(username="admin")
        student = User.objects.create_user(
            username="grade-2-two-subjects",
            password="strong-pass-123",
            full_name="Ikki fan o‘quvchisi",
            role=User.Role.STUDENT,
        )
        profile = StudentProfile.objects.create(
            student=student,
            grade=2,
            weekly_study_hours=5,
            assigned_admin=admin,
        )

        self.client.force_authenticate(admin)
        recommended = self.client.get(
            f"/api/student-profiles/{profile.id}/recommend-tests/"
        )
        self.assertEqual(recommended.status_code, 200)
        ids = {item["id"] for item in recommended.data["tests"]}
        self.assertIn(math_exam.id, ids)
        self.assertIn(english_exam.id, ids)

        for index, exam in enumerate((math_exam, english_exam), start=1):
            assigned = self.client.post(
                f"/api/exams/{exam.id}/assign-student/",
                {
                    "student": student.id,
                    "classroom": None,
                    "delivery_mode": "self",
                    "temporary_password": f"Subject{index}Pass",
                },
                format="json",
            )
            self.assertEqual(assigned.status_code, 200)

        self.assertEqual(
            ExamAssignment.objects.filter(student=student, is_active=True).count(),
            2,
        )

    def test_admin_cannot_assign_grade_2_exam_to_grade_3_student(self):
        admin = User.objects.get(username="admin")
        student = User.objects.create_user(
            username="grade-mismatch-student",
            password="strong-pass-123",
            full_name="Sinf mos emas",
            role=User.Role.STUDENT,
        )
        StudentProfile.objects.create(
            student=student,
            grade=3,
            weekly_study_hours=5,
            assigned_admin=admin,
        )
        exam = Exam.objects.get(
            title="RBIS Matematika Qabul Diagnostikasi - 2-sinf"
        )

        self.client.force_authenticate(admin)
        response = self.client.post(
            f"/api/exams/{exam.id}/assign-student/",
            {
                "student": student.id,
                "temporary_password": "MismatchPass",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("3-sinf", response.data["detail"])
