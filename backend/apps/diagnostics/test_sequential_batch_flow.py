from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

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
from apps.diagnostics.models import DiagnosticReport, ExamAssignment
from apps.profiling.models import StudentProfile


User = get_user_model()


@override_settings(DIAGNOSTIC_ACTIVE_SUBJECTS=("english", "math"))
class SequentialBatchDiagnosticTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="sequence-admin",
            password="strong-admin-pass",
            full_name="Sequence Admin",
            role=User.Role.ADMIN,
            is_staff=True,
        )
        self.student = User.objects.create_user(
            username="sequence-student",
            password="old-student-pass",
            full_name="Sequence Student",
            role=User.Role.STUDENT,
        )
        StudentProfile.objects.create(
            student=self.student,
            grade=3,
            assigned_admin=self.admin,
        )
        self.english_exam = self._create_exam(
            "english", "English", "English Placement 3", 3
        )
        self.math_exam = self._create_exam(
            "math", "Matematika", "Math Diagnostic 3", 3
        )

    def _create_exam(self, slug, subject_title, exam_title, grade):
        subject, _ = Subject.objects.get_or_create(
            slug=slug,
            defaults={"title": subject_title, "is_active": True},
        )
        topic, _ = Topic.objects.get_or_create(
            subject=subject,
            code=f"{slug}-sequence-topic",
            defaults={"title": f"{subject_title} topic"},
        )
        skill, _ = Skill.objects.get_or_create(
            subject=subject,
            slug=f"{slug}-sequence-skill",
            defaults={"title": f"{subject_title} skill"},
        )
        question = Question.objects.create(
            subject=subject,
            topic=topic,
            code=f"SEQ-{slug.upper()}-{grade}",
            prompt=f"{subject_title} question",
            explanation=f"{subject_title} explanation",
            difficulty=Question.Difficulty.BASIC,
            min_grade=grade,
            max_grade=grade,
            default_points=Decimal("100.00"),
            is_active=True,
            created_by=self.admin,
        )
        question.skills.add(skill)
        correct = QuestionOption.objects.create(
            question=question,
            label="A",
            text="Correct",
            is_correct=True,
            order=0,
        )
        QuestionOption.objects.create(
            question=question,
            label="B",
            text="Wrong",
            is_correct=False,
            order=1,
        )
        exam = Exam.objects.create(
            title=exam_title,
            grade=grade,
            purpose=Exam.Purpose.ADMISSION,
            duration_minutes=30,
            max_score=Decimal("100.00"),
            readiness_threshold=60,
            minimum_subject_score=50,
            starts_at=timezone.now(),
            ends_at=timezone.now() + timedelta(days=30),
            status=Exam.Status.ACTIVE,
            created_by=self.admin,
        )
        ExamSubjectWeight.objects.create(
            exam=exam,
            subject=subject,
            weight_percent=Decimal("100.00"),
            max_score=Decimal("100.00"),
        )
        exam_question = ExamQuestion.objects.create(
            exam=exam,
            question=question,
            points=Decimal("100.00"),
            order=1,
        )
        return exam, exam_question, correct

    def _answer_attempt(self, attempt_id, exam_question, correct_option):
        response = self.client.post(
            f"/api/attempts/{attempt_id}/answer/",
            {
                "exam_question": exam_question.id,
                "selected_option": correct_option.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)

    def test_first_test_starts_second_and_final_response_is_combined(self):
        self.client.force_authenticate(self.admin)
        assign = self.client.post(
            "/api/exams/assign-student-tests/",
            {
                "student": self.student.id,
                "exams": [self.english_exam[0].id, self.math_exam[0].id],
                "temporary_password": "SharedPass2026",
            },
            format="json",
        )
        self.assertEqual(assign.status_code, 201)

        assignments = list(
            ExamAssignment.objects.filter(student=self.student).order_by("batch_order")
        )
        self.assertEqual(len(assignments), 2)
        self.assertIsNotNone(assignments[0].batch_id)
        self.assertEqual(assignments[0].batch_id, assignments[1].batch_id)
        self.assertEqual([item.batch_order for item in assignments], [1, 2])
        self.assertTrue(all(item.batch_size == 2 for item in assignments))

        self.client.force_authenticate(self.student)
        start_first = self.client.post(
            f"/api/assignments/{assignments[0].id}/start/",
            {},
            format="json",
        )
        self.assertEqual(start_first.status_code, 201)
        first_attempt = start_first.data["id"]
        self._answer_attempt(
            first_attempt,
            self.english_exam[1],
            self.english_exam[2],
        )

        submit_first = self.client.post(
            f"/api/attempts/{first_attempt}/submit/",
            {},
            format="json",
        )
        self.assertEqual(submit_first.status_code, 200)
        self.assertEqual(submit_first.data["flow"], "next_test")
        self.assertEqual(
            submit_first.data["next_assignment"]["id"],
            assignments[1].id,
        )

        second_attempt = submit_first.data["next_attempt"]["id"]
        self._answer_attempt(
            second_attempt,
            self.math_exam[1],
            self.math_exam[2],
        )
        submit_second = self.client.post(
            f"/api/attempts/{second_attempt}/submit/",
            {},
            format="json",
        )
        self.assertEqual(submit_second.status_code, 200)
        self.assertEqual(submit_second.data["flow"], "complete")

        combined = submit_second.data["combined_report"]
        self.assertTrue(combined["is_combined"])
        self.assertEqual(len(combined["subject_results"]), 2)
        self.assertEqual(len(combined["component_reports"]), 2)
        self.assertEqual(Decimal(str(combined["overall_score"])), Decimal("100.00"))
        self.assertEqual(combined["answer_summary"]["correct"], 2)
        self.assertEqual(DiagnosticReport.objects.count(), 2)

        final_report_id = submit_second.data["report"]["id"]
        reopen = self.client.get(f"/api/reports/{final_report_id}/combined/")
        self.assertEqual(reopen.status_code, 200)
        self.assertTrue(reopen.data["is_combined"])
        self.assertEqual(len(reopen.data["question_review"]), 2)
