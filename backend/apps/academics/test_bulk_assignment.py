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
from apps.diagnostics.models import ExamAssignment
from apps.profiling.models import StudentProfile


User = get_user_model()


@override_settings(DIAGNOSTIC_ACTIVE_SUBJECTS=("english", "math"))
class BulkStudentAssignmentTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="bulk-admin",
            password="strong-admin-pass",
            full_name="Bulk Admin",
            role=User.Role.ADMIN,
            is_staff=True,
        )
        self.student = User.objects.create_user(
            username="grade-three-student",
            password="old-student-pass",
            full_name="Grade Three Student",
            role=User.Role.STUDENT,
        )
        StudentProfile.objects.create(
            student=self.student,
            grade=3,
            assigned_admin=self.admin,
        )
        self.english_exam = self._create_exam("english", "English", "English 3", 3)
        self.math_exam = self._create_exam("math", "Matematika", "Math 3", 3)
        self.client.force_authenticate(self.admin)

    def _create_exam(self, slug, subject_title, exam_title, grade):
        subject, _ = Subject.objects.get_or_create(
            slug=slug,
            defaults={"title": subject_title, "is_active": True},
        )
        topic, _ = Topic.objects.get_or_create(
            subject=subject,
            code=f"{slug}-bulk-topic",
            defaults={"title": f"{subject_title} topic"},
        )
        skill, _ = Skill.objects.get_or_create(
            subject=subject,
            slug=f"{slug}-bulk-skill",
            defaults={"title": f"{subject_title} skill"},
        )
        question = Question.objects.create(
            subject=subject,
            topic=topic,
            code=f"BULK-{slug.upper()}-{grade}",
            prompt=f"{subject_title} question",
            explanation="Test explanation",
            difficulty=Question.Difficulty.BASIC,
            min_grade=grade,
            max_grade=grade,
            default_points=Decimal("100.00"),
            is_active=True,
            created_by=self.admin,
        )
        question.skills.add(skill)
        QuestionOption.objects.create(
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
            description="Bulk assignment regression test",
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
        ExamQuestion.objects.create(
            exam=exam,
            question=question,
            points=Decimal("100.00"),
            order=1,
        )
        return exam

    def test_admin_assigns_math_and_english_with_one_password(self):
        response = self.client.post(
            "/api/exams/assign-student-tests/",
            {
                "student": self.student.id,
                "exams": [self.english_exam.id, self.math_exam.id],
                "temporary_password": "SharedPass2026",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["assignments"]), 2)
        self.assertEqual(
            ExamAssignment.objects.filter(student=self.student, is_active=True).count(),
            2,
        )
        self.student.refresh_from_db()
        self.assertTrue(self.student.check_password("SharedPass2026"))

    def test_bulk_assignment_rejects_wrong_grade_atomically(self):
        grade_four_exam = self._create_exam("english", "English", "English 4", 4)
        response = self.client.post(
            "/api/exams/assign-student-tests/",
            {
                "student": self.student.id,
                "exams": [self.math_exam.id, grade_four_exam.id],
                "temporary_password": "SharedPass2026",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            ExamAssignment.objects.filter(student=self.student).count(),
            0,
        )
        self.student.refresh_from_db()
        self.assertTrue(self.student.check_password("old-student-pass"))
