from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.accounts.models import Classroom, ParentStudent
from apps.academics.models import Exam, Question
from apps.pathways.models import Certificate, UniversityGoal

from .models import DiagnosticReport, ExamAssignment, ExamAttempt


User = get_user_model()


@override_settings(DEBUG=True)
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

    def test_student_cannot_self_verify_certificate_with_patch(self):
        self.authenticate()
        certificate = Certificate.objects.filter(is_verified=False).first()
        if certificate is None:
            goal = UniversityGoal.objects.get()
            certificate = Certificate.objects.create(
                student=goal.student,
                kind=Certificate.Kind.OTHER,
                title="Portfolio",
                score=80,
                issued_at=timezone.localdate(),
            )
        response = self.client.patch(
            f"/api/certificates/{certificate.id}/",
            {"is_verified": True},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        certificate.refresh_from_db()
        self.assertFalse(certificate.is_verified)

    def test_teacher_can_verify_only_own_class_certificate(self):
        student = User.objects.get(username="student")
        certificate = Certificate.objects.create(
            student=student,
            kind=Certificate.Kind.OTHER,
            title="Portfolio",
            score=80,
            issued_at=timezone.localdate(),
        )
        self.authenticate("teacher", "teacher123")
        response = self.client.post(f"/api/certificates/{certificate.id}/verify/", {}, format="json")
        self.assertEqual(response.status_code, 200)
        certificate.refresh_from_db()
        self.assertTrue(certificate.is_verified)
        self.assertEqual(certificate.verified_by.username, "teacher")

    def test_parent_cannot_create_student_link(self):
        outsider = User.objects.create_user(
            username="outsider",
            password="strong-pass-123",
            full_name="Outside Student",
            role=User.Role.STUDENT,
        )
        parent = User.objects.get(username="parent")
        self.authenticate("parent", "parent123")
        response = self.client.post(
            "/api/parent-students/",
            {"parent": parent.id, "student": outsider.id, "relationship": "Ota-ona"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(ParentStudent.objects.filter(parent=parent, student=outsider).exists())

    def test_student_cannot_update_or_delete_assignment(self):
        assignment = ExamAssignment.objects.get(student__username="student")
        self.authenticate()
        update_response = self.client.patch(
            f"/api/assignments/{assignment.id}/",
            {"is_active": False},
            format="json",
        )
        delete_response = self.client.delete(f"/api/assignments/{assignment.id}/")
        self.assertEqual(update_response.status_code, 403)
        self.assertEqual(delete_response.status_code, 403)
        assignment.refresh_from_db()
        self.assertTrue(assignment.is_active)

    def test_teacher_cannot_assign_exam_to_student_outside_own_class(self):
        outsider = User.objects.create_user(
            username="outside-class",
            password="strong-pass-123",
            full_name="Outside Class",
            role=User.Role.STUDENT,
        )
        exam = Exam.objects.first()
        self.authenticate("teacher", "teacher123")
        response = self.client.post(
            "/api/assignments/",
            {"exam": exam.id, "student": outsider.id, "delivery_mode": "self", "is_active": True},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(ExamAssignment.objects.filter(exam=exam, student=outsider).exists())

    def test_student_exam_payload_hides_answer_explanation(self):
        self.authenticate()
        response = self.client.get("/api/assignments/")
        self.assertEqual(response.status_code, 200)
        question = response.data["results"][0]["exam_detail"]["exam_questions"][0]["question_detail"]
        self.assertNotIn("explanation", question)
        self.assertNotIn("is_correct", question["options"][0])

    def test_admin_question_payload_keeps_answer_fields(self):
        self.authenticate("admin", "admin12345")
        response = self.client.get("/api/questions/")
        self.assertEqual(response.status_code, 200)
        question = response.data["results"][0]
        self.assertIn("explanation", question)
        self.assertIn("is_correct", question["options"][0])

    def test_answered_question_option_edit_returns_400_instead_of_500(self):
        question = Question.objects.filter(options__student_selections__isnull=False).distinct().first()
        self.authenticate("admin", "admin12345")
        options = [
            {
                "label": item.label,
                "text": item.text,
                "is_correct": item.is_correct,
                "order": item.order,
            }
            for item in question.options.all()
        ]
        options[0]["text"] = f"{options[0]['text']} updated"
        response = self.client.patch(
            f"/api/questions/{question.id}/",
            {"options": options},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_answered_exam_question_edit_returns_400_instead_of_500(self):
        exam = DiagnosticReport.objects.get().attempt.assignment.exam
        self.authenticate("admin", "admin12345")
        questions = [
            {"question": item.question_id, "points": str(item.points), "order": item.order}
            for item in exam.exam_questions.all()
        ][:-1]
        response = self.client.patch(
            f"/api/exams/{exam.id}/",
            {"exam_questions": questions},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_university_goal_student_cannot_be_reassigned(self):
        goal = UniversityGoal.objects.get()
        outsider = User.objects.create_user(
            username="goal-outsider",
            password="strong-pass-123",
            full_name="Goal Outsider",
            role=User.Role.STUDENT,
        )
        self.authenticate("parent", "parent123")
        response = self.client.patch(
            f"/api/university-goals/{goal.id}/",
            {"student": outsider.id},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        goal.refresh_from_db()
        self.assertNotEqual(goal.student_id, outsider.id)

    def test_admin_report_detail_contains_saved_answers_and_analysis(self):
        report = DiagnosticReport.objects.get()
        self.authenticate("admin", "admin12345")
        response = self.client.get(f"/api/reports/{report.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertGreater(response.data["answer_summary"]["total"], 0)
        self.assertEqual(
            response.data["answer_summary"]["total"],
            len(response.data["question_review"]),
        )
        self.assertIn("selected_option", response.data["question_review"][0])
        self.assertIn("correct_option", response.data["question_review"][0])
        self.assertIn("attempt_detail", response.data)
        self.assertIn("strengths", response.data)
        self.assertIn("weaknesses", response.data)

    def test_student_report_detail_does_not_expose_answer_key(self):
        report = DiagnosticReport.objects.get()
        self.authenticate()
        response = self.client.get(f"/api/reports/{report.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("correct_option", response.data["question_review"][0])
        self.assertNotIn("explanation", response.data["question_review"][0])

    def test_admin_can_filter_reports_by_grade_subject_and_score(self):
        self.authenticate("admin", "admin12345")
        matching = self.client.get("/api/reports/?grade=8&subject=math&score_min=40&score_max=50")
        wrong_grade = self.client.get("/api/reports/?grade=5")
        self.assertEqual(matching.status_code, 200)
        self.assertEqual(matching.data["count"], 1)
        self.assertEqual(wrong_grade.status_code, 200)
        self.assertEqual(wrong_grade.data["count"], 0)

    def test_admin_reassigns_without_deleting_historical_report(self):
        report = DiagnosticReport.objects.get()
        old_assignment = report.attempt.assignment
        self.authenticate("admin", "admin12345")
        response = self.client.post(f"/api/reports/{report.id}/reassign/", {}, format="json")
        self.assertEqual(response.status_code, 201)
        old_assignment.refresh_from_db()
        self.assertFalse(old_assignment.is_active)
        self.assertTrue(
            ExamAssignment.objects.filter(
                id=response.data["id"],
                exam=old_assignment.exam,
                student=old_assignment.student,
                is_active=True,
            ).exists()
        )
        self.assertTrue(DiagnosticReport.objects.filter(id=report.id).exists())

    def test_admin_can_compare_two_attempts_for_same_student(self):
        original = DiagnosticReport.objects.get()
        old_assignment = original.attempt.assignment
        old_assignment.is_active = False
        old_assignment.save(update_fields=["is_active"])
        new_assignment = ExamAssignment.objects.create(
            exam=old_assignment.exam,
            student=old_assignment.student,
            classroom=old_assignment.classroom,
            assigned_by=old_assignment.assigned_by,
            is_active=True,
        )
        attempt = ExamAttempt.objects.create(
            assignment=new_assignment,
            status=ExamAttempt.Status.SUBMITTED,
            expires_at=timezone.now(),
            submitted_at=timezone.now(),
            overall_score=60,
            earned_points=2,
            is_ready=False,
        )
        current = DiagnosticReport.objects.create(
            attempt=attempt,
            overall_score=60,
            range_low=57,
            range_high=63,
            expected_score=60,
            readiness=DiagnosticReport.Readiness.NOT_READY,
        )
        self.authenticate("admin", "admin12345")
        response = self.client.get(f"/api/reports/{current.id}/compare/?other={original.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["previous"]["id"], original.id)
        self.assertEqual(response.data["overall_delta"], 18.75)

    @override_settings(DEBUG=False)
    def test_seed_demo_is_blocked_outside_debug(self):
        with self.assertRaises(CommandError):
            call_command("seed_demo", verbosity=0)


@override_settings(DEBUG=True)
class AdministeredProfilingFlowTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", verbosity=0)

    def setUp(self):
        token = self.client.post(
            "/api/auth/token/",
            {"username": "admin", "password": "admin12345"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.data['access']}")

    def test_admin_can_run_full_profile_to_roadmap_flow(self):
        category = self.client.get("/api/categories/?code=presidential-school").data["results"][0]
        onboard = self.client.post(
            "/api/student-profiles/onboard/",
            {
                "username": "new-student",
                "password": "student123",
                "full_name": "Ali Valiyev",
                "phone": "+998901112233",
                "email": "",
                "birth_date": "2013-05-10",
                "school_name": "15-maktab",
                "grade": 8,
                "region": "Sirdaryo",
                "district": "Yangiyer",
                "weekly_study_hours": 9,
                "guardian_name": "Vali Valiyev",
                "guardian_phone": "+998909998877",
                "guardian_relationship": "Ota",
            },
            format="json",
        )
        self.assertEqual(onboard.status_code, 201)
        profile_id = onboard.data["id"]
        student_id = onboard.data["student"]["id"]

        interview = self.client.post(
            "/api/student-interviews/",
            {
                "profile": profile_id,
                "strengths": "Mantiq",
                "weaknesses": "Algebra",
                "main_problem": "Poydevor",
                "motivation_level": "high",
                "independence_level": "medium",
                "parent_support_level": "high",
                "admin_summary": "Poydevorni mustahkamlash kerak.",
                "next_step": "Diagnostika",
                "answers": [],
            },
            format="json",
        )
        self.assertEqual(interview.status_code, 201)
        goal = self.client.post(
            "/api/student-goals/",
            {
                "profile": profile_id,
                "goal_type": "presidential_school",
                "title": "Prezident maktabiga kirish",
                "target_score": 88,
                "priority": 1,
                "is_primary": True,
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(goal.status_code, 201)
        link = self.client.post(
            "/api/student-categories/",
            {
                "profile": profile_id,
                "category": category["id"],
                "source": "interview",
                "confidence": 95,
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(link.status_code, 201)
        completed = self.client.post(f"/api/student-profiles/{profile_id}/complete-interview/", {}, format="json")
        self.assertEqual(completed.status_code, 200)

        recommendation = self.client.get(f"/api/student-profiles/{profile_id}/recommend-tests/")
        self.assertEqual(recommendation.status_code, 200)
        self.assertGreater(len(recommendation.data["tests"]), 0)
        exam = recommendation.data["tests"][0]

        assignment = self.client.post(
            f"/api/exams/{exam['id']}/assign-student/",
            {"student": student_id, "classroom": None, "delivery_mode": "administered"},
            format="json",
        )
        self.assertEqual(assignment.status_code, 200)
        started = self.client.post(f"/api/assignments/{assignment.data['assignment']}/start/", {}, format="json")
        self.assertEqual(started.status_code, 201)
        attempt_id = started.data["id"]

        for exam_question in exam["exam_questions"]:
            correct_option = exam_question["question_detail"]["options"][0]
            answer = self.client.post(
                f"/api/attempts/{attempt_id}/answer/",
                {
                    "exam_question": exam_question["id"],
                    "selected_option": correct_option["id"],
                    "is_flagged": False,
                },
                format="json",
            )
            self.assertEqual(answer.status_code, 200)

        report = self.client.post(f"/api/attempts/{attempt_id}/submit/", {}, format="json")
        self.assertEqual(report.status_code, 200)
        self.assertEqual(report.data["student"]["id"], student_id)
        self.assertEqual(report.data["roadmap"]["weekly_hours"], 9)
        self.assertEqual(report.data["roadmap"]["primary_goal_title"], "Prezident maktabiga kirish")
        self.assertEqual(report.data["roadmap"]["generation_context"]["grade"], 8)
