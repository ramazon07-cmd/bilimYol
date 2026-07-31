from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.academics.models import Exam

from .models import ExamAssignment


User = get_user_model()


@override_settings(DEBUG=True)
class AttemptAutosaveContractTests(APITestCase):
    """Autosave response yengil qolishini tekshiradi."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", verbosity=0)
        call_command("seed_english_diagnostics", verbosity=0)

        cls.student = User.objects.create_user(
            username="performance-student",
            password="performance-pass-123",
            full_name="Performance Student",
            role=User.Role.STUDENT,
        )
        cls.admin = User.objects.get(username="admin")
        cls.exam = Exam.objects.get(title="RBIS English Placement - 8-sinf")
        cls.assignment = ExamAssignment.objects.create(
            exam=cls.exam,
            student=cls.student,
            assigned_by=cls.admin,
            is_active=True,
        )

    def authenticate(self):
        token = self.client.post(
            "/api/auth/token/",
            {"username": "performance-student", "password": "performance-pass-123"},
            format="json",
        )
        self.assertEqual(token.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.data['access']}")

    def test_answer_endpoint_returns_lightweight_ack(self):
        self.authenticate()
        started = self.client.post(f"/api/assignments/{self.assignment.id}/start/", {}, format="json")
        self.assertEqual(started.status_code, 201)

        exam_question = self.exam.exam_questions.select_related("question").first()
        option = exam_question.question.options.first()
        saved = self.client.post(
            f"/api/attempts/{started.data['id']}/answer/",
            {
                "exam_question": exam_question.id,
                "selected_option": option.id,
                "is_flagged": False,
            },
            format="json",
        )

        self.assertEqual(saved.status_code, 200)
        self.assertEqual(saved.data["exam_question"], exam_question.id)
        self.assertEqual(saved.data["selected_option"], option.id)
        self.assertNotIn("answers", saved.data)
        self.assertNotIn("assignment_detail", saved.data)
