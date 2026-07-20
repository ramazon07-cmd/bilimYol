from django.core.management import call_command
from rest_framework.test import APITestCase

from apps.accounts.models import Classroom
from apps.academics.models import Exam
from apps.pathways.models import Certificate, UniversityGoal

from .models import DiagnosticReport


class BilimYolApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", verbosity=0)

    def authenticate(self, username="student", password="student123"):
        token = self.client.post("/api/auth/token/", {"username": username, "password": password}, format="json")
        self.assertEqual(token.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.data['access']}")

    def test_student_can_open_own_report(self):
        self.authenticate()
        response = self.client.get("/api/reports/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["readiness"], "not_ready")

    def test_demo_weighted_score_is_41_25(self):
        report = DiagnosticReport.objects.get()
        self.assertEqual(float(report.overall_score), 41.25)
        self.assertEqual(report.subject_results.count(), 3)
        self.assertEqual(report.roadmap.stages.count(), 3)

    def test_student_cannot_manage_users(self):
        self.authenticate()
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, 403)

    def test_each_role_opens_its_own_dashboard(self):
        accounts = [
            ("student", "student123", "student"),
            ("parent", "parent123", "parent"),
            ("teacher", "teacher123", "teacher"),
            ("admin", "admin12345", "admin"),
        ]
        for username, password, role in accounts:
            self.client.credentials()
            self.authenticate(username, password)
            me = self.client.get("/api/auth/me/")
            dashboard = self.client.get("/api/dashboard/")
            self.assertEqual(me.status_code, 200)
            self.assertEqual(dashboard.status_code, 200)
            self.assertEqual(me.data["role"], role)
            self.assertEqual(dashboard.data["role"], role)

    def test_every_demo_test_subject_is_normalized_to_100(self):
        for exam in Exam.objects.all():
            self.assertEqual(float(exam.max_score), 100)
            self.assertEqual(sum(float(item.weight_percent) for item in exam.subject_weights.all()), 100)
            self.assertTrue(all(float(item.max_score) == 100 for item in exam.subject_weights.all()))
            self.assertSetEqual(set(exam.subject_weights.values_list("subject__slug", flat=True)), {"iq", "math", "english"})

    def test_admin_can_assign_grade_test_to_whole_class(self):
        self.authenticate("admin", "admin12345")
        classroom = Classroom.objects.get(name="8-A")
        exam = Exam.objects.get(title="8-A · IQ / Math / English Mock #1")
        response = self.client.post(f"/api/exams/{exam.id}/assign-class/", {"classroom": classroom.id}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["students"], 1)
        self.assertEqual(exam.assignments.filter(classroom=classroom, is_active=True).count(), 1)

    def test_class_endpoint_returns_only_matching_test(self):
        self.authenticate("admin", "admin12345")
        classroom = Classroom.objects.get(name="6-A")
        response = self.client.get(f"/api/exams/by-class/?classroom={classroom.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["classroom"]["grade"], 6)
        self.assertEqual(len(response.data["tests"]), 1)

    def test_parent_sees_dream_university_progress_from_mock_and_certificates(self):
        self.authenticate("parent", "parent123")
        response = self.client.get("/api/university-goals/")
        self.assertEqual(response.status_code, 200)
        goal = response.data["results"][0]
        requirements = {item["key"]: item for item in goal["progress"]["requirements"]}
        self.assertEqual(requirements["ielts"]["progress"], 100.0)
        self.assertGreater(requirements["sat"]["progress"], 99)
        self.assertEqual(requirements["math"]["current"], 25.0)

    def test_parent_can_change_linked_child_university(self):
        self.authenticate("parent", "parent123")
        goal = UniversityGoal.objects.select_related("student").get()
        other_university_id = goal.university.__class__.objects.exclude(id=goal.university_id).first().id
        response = self.client.patch(f"/api/university-goals/{goal.id}/", {"university": other_university_id}, format="json")
        self.assertEqual(response.status_code, 200)
        goal.refresh_from_db()
        self.assertEqual(goal.university_id, other_university_id)

    def test_student_certificate_upload_stays_unverified(self):
        self.authenticate()
        goal = UniversityGoal.objects.select_related("student").get()
        response = self.client.post(
            "/api/certificates/",
            {"student": goal.student_id, "kind": "other", "title": "Olympiad", "score": 88, "issued_at": "2026-05-01", "is_verified": True},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertFalse(Certificate.objects.get(id=response.data["id"]).is_verified)
