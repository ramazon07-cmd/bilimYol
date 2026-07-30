from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.accounts.models import ClassroomStudent, ParentStudent
from apps.communications.models import Conversation, Message, Notification
from apps.diagnostics.models import Roadmap, WeeklyTask
from apps.pathways.models import Certificate, University, UniversityGoal


User = get_user_model()


@override_settings(DEBUG=True)
class P4BackendIntegrationTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", verbosity=0)
        cls.admin = User.objects.get(username="admin")
        cls.teacher = User.objects.get(username="teacher")
        cls.student = User.objects.get(username="student")
        cls.parent = User.objects.get(username="parent")
        cls.other_parent = User.objects.create_user(
            username="other-parent",
            password="strong-pass-123",
            full_name="Boshqa ota-ona",
            role=User.Role.PARENT,
        )
        cls.other_student = User.objects.create_user(
            username="other-student",
            password="strong-pass-123",
            full_name="Boshqa o‘quvchi",
            role=User.Role.STUDENT,
        )
        ParentStudent.objects.create(parent=cls.other_parent, student=cls.other_student)
        classroom = cls.student.classrooms.first()
        ClassroomStudent.objects.create(classroom=classroom, student=cls.other_student)

    def login(self, user):
        self.client.force_authenticate(user)

    def test_parent_classroom_payload_contains_only_own_child(self):
        self.login(self.parent)
        classroom = self.student.classrooms.first()
        result = self.client.get(f"/api/classrooms/{classroom.id}/")
        self.assertEqual(result.status_code, 200)
        self.assertEqual([item["student"] for item in result.data["enrollments"]], [self.student.id])
        self.assertEqual(result.data["student_count"], 1)

    def test_parent_cannot_see_another_family_certificate(self):
        Certificate.objects.create(
            student=self.other_student,
            kind=Certificate.Kind.OTHER,
            title="Boshqa sertifikat",
            score=90,
            issued_at=timezone.localdate(),
        )
        self.login(self.parent)
        result = self.client.get("/api/certificates/?page_size=100")
        ids = [item["student"] for item in result.data["results"]]
        self.assertNotIn(self.other_student.id, ids)
        self.assertTrue(all(student_id == self.student.id for student_id in ids))

    def test_roadmap_approval_persists_and_notifies_family(self):
        roadmap = Roadmap.objects.get(student=self.student)
        self.login(self.teacher)
        result = self.client.post(f"/api/roadmaps/{roadmap.id}/approve/", {}, format="json")
        self.assertEqual(result.status_code, 200)
        roadmap.refresh_from_db()
        self.assertEqual(roadmap.status, Roadmap.Status.APPROVED)
        self.assertEqual(roadmap.teacher, self.teacher)
        self.assertTrue(Notification.objects.filter(
            recipient=self.parent,
            kind=Notification.Kind.ROADMAP,
            metadata__roadmap_id=roadmap.id,
        ).exists())

    def test_university_change_persists_and_notifies_student(self):
        goal = UniversityGoal.objects.get(student=self.student)
        university = University.objects.exclude(id=goal.university_id).first()
        self.login(self.parent)
        result = self.client.patch(
            f"/api/university-goals/{goal.id}/",
            {"university": university.id},
            format="json",
        )
        self.assertEqual(result.status_code, 200)
        goal.refresh_from_db()
        self.assertEqual(goal.university, university)
        self.assertTrue(Notification.objects.filter(
            recipient=self.student,
            kind=Notification.Kind.UNIVERSITY,
        ).exists())

    def test_certificate_pending_reject_and_resubmit_flow(self):
        self.login(self.student)
        created = self.client.post(
            "/api/certificates/",
            {
                "student": self.student.id,
                "kind": Certificate.Kind.IELTS,
                "title": "IELTS Academic",
                "score": 6.5,
                "issued_at": str(timezone.localdate()),
            },
            format="json",
        )
        self.assertEqual(created.status_code, 201)
        certificate_id = created.data["id"]
        self.assertEqual(created.data["verification_status"], Certificate.VerificationStatus.PENDING)

        self.login(self.teacher)
        rejected = self.client.post(
            f"/api/certificates/{certificate_id}/reject/",
            {"note": "Hujjat havolasi yetishmaydi."},
            format="json",
        )
        self.assertEqual(rejected.status_code, 200)
        self.assertEqual(rejected.data["verification_status"], Certificate.VerificationStatus.REJECTED)

        self.login(self.student)
        resubmitted = self.client.patch(
            f"/api/certificates/{certificate_id}/",
            {"file_url": "https://example.com/certificate.pdf"},
            format="json",
        )
        self.assertEqual(resubmitted.status_code, 200)
        self.assertEqual(resubmitted.data["verification_status"], Certificate.VerificationStatus.PENDING)

        self.login(self.teacher)
        verified = self.client.post(
            f"/api/certificates/{certificate_id}/verify/",
            {"note": "Tekshirildi."},
            format="json",
        )
        self.assertEqual(verified.status_code, 200)
        self.assertTrue(verified.data["is_verified"])
        self.assertEqual(verified.data["verification_status"], Certificate.VerificationStatus.VERIFIED)

    def test_parent_message_and_teacher_notification_persist(self):
        conversation = Conversation.objects.get(parent=self.parent, kind=Conversation.Kind.TEACHER)
        self.login(self.parent)
        result = self.client.post(
            "/api/messages/",
            {"conversation": conversation.id, "body": "Roadmap vazifalarini ko‘rdim."},
            format="json",
        )
        self.assertEqual(result.status_code, 201)
        self.assertTrue(Message.objects.filter(
            conversation=conversation,
            sender=self.parent,
            body="Roadmap vazifalarini ko‘rdim.",
        ).exists())
        self.assertTrue(Notification.objects.filter(
            recipient=self.teacher,
            kind=Notification.Kind.MESSAGE,
            metadata__conversation_id=conversation.id,
        ).exists())

    def test_parent_can_complete_only_parent_roadmap_task(self):
        roadmap = Roadmap.objects.get(student=self.student)
        parent_task = WeeklyTask.objects.filter(
            stage__roadmap=roadmap,
            audience=WeeklyTask.Audience.PARENT,
        ).first()
        student_task = WeeklyTask.objects.filter(
            stage__roadmap=roadmap,
            audience=WeeklyTask.Audience.STUDENT,
        ).first()
        self.login(self.parent)
        completed = self.client.patch(
            f"/api/weekly-tasks/{parent_task.id}/",
            {"is_completed": True},
            format="json",
        )
        self.assertEqual(completed.status_code, 200)
        parent_task.refresh_from_db()
        self.assertTrue(parent_task.is_completed)

        forbidden = self.client.patch(
            f"/api/weekly-tasks/{student_task.id}/",
            {"is_completed": True},
            format="json",
        )
        self.assertEqual(forbidden.status_code, 403)

    def test_notification_mark_read_and_mark_all_read(self):
        Notification.objects.create(
            recipient=self.parent,
            title="Birinchi",
            kind=Notification.Kind.SYSTEM,
        )
        second = Notification.objects.create(
            recipient=self.parent,
            title="Ikkinchi",
            kind=Notification.Kind.SYSTEM,
        )
        self.login(self.parent)
        result = self.client.post(f"/api/notifications/{second.id}/mark-read/", {}, format="json")
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.data["is_read"])
        result = self.client.post("/api/notifications/mark-all-read/", {}, format="json")
        self.assertEqual(result.status_code, 200)
        self.assertFalse(Notification.objects.filter(recipient=self.parent, is_read=False).exists())

    def test_page_size_query_parameter_returns_requested_family_records(self):
        Notification.objects.bulk_create([
            Notification(
                recipient=self.parent,
                title=f"Xabarnoma {index}",
                kind=Notification.Kind.SYSTEM,
            )
            for index in range(35)
        ])
        self.login(self.parent)
        result = self.client.get("/api/notifications/?page_size=50")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(result.data["results"]), result.data["count"])
        self.assertGreaterEqual(result.data["count"], 35)
