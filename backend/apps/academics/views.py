import uuid

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.utils.crypto import get_random_string
from rest_framework import decorators, response, status, viewsets

from apps.accounts.permissions import IsAdminRole, IsTeacherOrAdmin, ReadOnlyOrAdmin
from apps.accounts.models import Classroom
from apps.diagnostics.models import ExamAssignment
from apps.communications.models import Notification
from apps.communications.services import notify_users

from .models import Exam, Question, Skill, Subject, Topic
from .policies import enabled_diagnostic_exams
from .serializers import ExamSerializer, QuestionSerializer, SkillSerializer, SubjectSerializer, TopicSerializer


User = get_user_model()


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [ReadOnlyOrAdmin]
    filterset_fields = ["is_active"]
    search_fields = ["title", "slug"]


class TopicViewSet(viewsets.ModelViewSet):
    serializer_class = TopicSerializer
    permission_classes = [ReadOnlyOrAdmin]
    filterset_fields = ["subject", "parent"]
    search_fields = ["title", "code", "description"]

    def get_queryset(self):
        return Topic.objects.select_related("subject", "parent").prefetch_related("prerequisites")


class SkillViewSet(viewsets.ModelViewSet):
    serializer_class = SkillSerializer
    permission_classes = [ReadOnlyOrAdmin]
    filterset_fields = ["subject"]
    search_fields = ["title", "slug"]

    def get_queryset(self):
        return Skill.objects.select_related("subject")


class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer
    permission_classes = [IsTeacherOrAdmin]
    filterset_fields = ["subject", "topic", "difficulty", "min_grade", "max_grade", "is_active"]
    search_fields = ["code", "prompt", "topic__title", "skills__title"]
    ordering_fields = ["code", "created_at", "difficulty"]

    def get_permissions(self):
        permission_classes = (
            [IsTeacherOrAdmin]
            if self.request.method in {"GET", "HEAD", "OPTIONS"}
            else [IsAdminRole]
        )
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        return Question.objects.select_related("subject", "topic").prefetch_related("skills", "options")


class ExamViewSet(viewsets.ModelViewSet):
    serializer_class = ExamSerializer
    permission_classes = [ReadOnlyOrAdmin]
    filterset_fields = ["status", "grade", "purpose", "target_classrooms", "recommended_categories"]
    search_fields = ["title", "description"]
    ordering_fields = ["starts_at", "created_at"]

    def get_queryset(self):
        queryset = Exam.objects.select_related("created_by").prefetch_related("target_classrooms", "recommended_categories", "subject_weights__subject", "exam_questions__question__options", "exam_questions__question__skills")
        queryset = enabled_diagnostic_exams(queryset)
        if self.request.user.role == "student":
            return queryset.exclude(status=Exam.Status.DRAFT)
        return queryset

    @decorators.action(detail=True, methods=["post"], permission_classes=[IsAdminRole])
    def publish(self, request, pk=None):
        exam = self.get_object()
        if not exam.exam_questions.exists() or not exam.subject_weights.exists():
            return response.Response({"detail": "Savollar va fan og‘irliklarini kiriting."}, status=status.HTTP_400_BAD_REQUEST)
        exam.status = Exam.Status.SCHEDULED if exam.starts_at else Exam.Status.ACTIVE
        exam.save(update_fields=["status", "updated_at"])
        return response.Response(self.get_serializer(exam).data)

    @decorators.action(detail=False, methods=["get"], url_path="by-class")
    def by_class(self, request):
        classroom_id = request.query_params.get("classroom")
        if not classroom_id:
            return response.Response({"detail": "classroom parametri majburiy."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            classroom = Classroom.objects.get(id=classroom_id)
        except (Classroom.DoesNotExist, ValueError):
            return response.Response({"detail": "Sinf topilmadi."}, status=status.HTTP_404_NOT_FOUND)
        queryset = self.get_queryset().filter(grade=classroom.grade).filter(target_classrooms=classroom).distinct()
        return response.Response({
            "classroom": {"id": classroom.id, "name": classroom.name, "grade": classroom.grade},
            "tests": self.get_serializer(queryset, many=True).data,
        })

    @decorators.action(detail=True, methods=["post"], permission_classes=[IsAdminRole], url_path="assign-class")
    @transaction.atomic
    def assign_class(self, request, pk=None):
        exam = self.get_object()
        classroom_id = request.data.get("classroom")
        try:
            classroom = Classroom.objects.prefetch_related("students").get(id=classroom_id)
        except (Classroom.DoesNotExist, ValueError, TypeError):
            return response.Response({"detail": "Sinf topilmadi."}, status=status.HTTP_404_NOT_FOUND)
        if classroom.grade != exam.grade:
            return response.Response({"detail": "Test va sinf bosqichi mos emas."}, status=status.HTTP_400_BAD_REQUEST)
        exam.target_classrooms.add(classroom)
        created = 0
        for student in classroom.students.all():
            assignment = ExamAssignment.objects.filter(exam=exam, student=student, is_active=True).first()
            was_created = assignment is None
            if assignment is None:
                assignment = ExamAssignment(exam=exam, student=student)
            assignment.classroom = classroom
            assignment.available_from = request.data.get("available_from") or timezone.now()
            assignment.due_at = request.data.get("due_at") or exam.ends_at
            assignment.is_active = True
            assignment.assigned_by = request.user
            assignment.delivery_mode = ExamAssignment.DeliveryMode.SELF
            assignment.administered_by = None
            assignment.save()
            notify_users(
                [student],
                kind=Notification.Kind.ASSIGNMENT,
                title="Yangi diagnostika testi biriktirildi",
                message=exam.title,
                action_path="test",
                metadata={"assignment_id": assignment.id},
            )
            created += int(was_created)
        return response.Response({
            "detail": f"{classroom.name} sinfiga test biriktirildi.",
            "students": classroom.students.count(),
            "new_assignments": created,
        })

    @decorators.action(detail=True, methods=["post"], permission_classes=[IsAdminRole], url_path="assign-student")
    def assign_student(self, request, pk=None):
        exam = self.get_object()
        student_id = request.data.get("student")
        classroom_id = request.data.get("classroom")
        requested_password = str(request.data.get("temporary_password") or "").strip()

        try:
            student = User.objects.get(id=student_id, role=User.Role.STUDENT)
        except (User.DoesNotExist, ValueError, TypeError):
            return response.Response({"detail": "O‘quvchi topilmadi."}, status=status.HTTP_404_NOT_FOUND)

        classroom = None
        if classroom_id:
            try:
                classroom = Classroom.objects.get(id=classroom_id)
            except (Classroom.DoesNotExist, ValueError, TypeError):
                return response.Response({"detail": "Sinf topilmadi."}, status=status.HTTP_404_NOT_FOUND)
            if not classroom.students.filter(id=student.id).exists():
                return response.Response({"detail": "O‘quvchi bu sinfga biriktirilmagan."}, status=status.HTTP_400_BAD_REQUEST)

        profile = getattr(student, "student_profile", None)
        profile_grade = profile.grade if profile else None
        classroom_grade = classroom.grade if classroom else None
        enrolled_grade = student.classrooms.filter(is_active=True).values_list("grade", flat=True).first()
        student_grade = profile_grade or classroom_grade or enrolled_grade
        if exam.grade is not None and student_grade is None:
            return response.Response(
                {"detail": "O‘quvchining sinfi belgilanmagan. Avval profil yoki sinfni to‘ldiring."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if exam.grade is not None and exam.grade != student_grade:
            return response.Response(
                {"detail": f"Test {exam.grade}-sinf uchun, o‘quvchi esa {student_grade}-sinfda."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        temporary_password = None
        password_changed = False
        if not student.has_usable_password():
            if requested_password and len(requested_password) < 8:
                return response.Response(
                    {"detail": "Vaqtinchalik parol kamida 8 belgidan iborat bo‘lishi kerak."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            temporary_password = requested_password or get_random_string(
                10,
                allowed_chars="abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789",
            )
            student.set_password(temporary_password)
            student.save(update_fields=["password"])
            password_changed = True

        assignment = ExamAssignment.objects.filter(exam=exam, student=student, is_active=True).first()
        created = assignment is None
        if assignment is None:
            assignment = ExamAssignment(exam=exam, student=student)
        assignment.classroom = classroom
        assignment.is_active = True
        assignment.assigned_by = request.user
        assignment.delivery_mode = ExamAssignment.DeliveryMode.SELF
        assignment.administered_by = None
        assignment.save()
        if profile:
            profile.status = profile.Status.TEST_ASSIGNED
            profile.save(update_fields=["status", "updated_at"])
        notify_users(
            [student],
            kind=Notification.Kind.ASSIGNMENT,
            title="Yangi diagnostika testi biriktirildi",
            message=exam.title,
            action_path="test",
            metadata={"assignment_id": assignment.id},
        )
        return response.Response({
            "assignment": assignment.id,
            "created": created,
            "student": student.full_name,
            "delivery_mode": assignment.delivery_mode,
            "credentials": {
                "username": student.username,
                "temporary_password": temporary_password,
                "password_changed": password_changed,
            },
        })

    @decorators.action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAdminRole],
        url_path="assign-student-tests",
    )
    @transaction.atomic
    def assign_student_tests(self, request):
        """Assign several exact-grade diagnostic tests with one shared login password."""
        # bilimyol-bulk-tests-minimal-login-v5
        raw_exam_ids = request.data.get("exams") or []
        student_id = request.data.get("student")
        classroom_id = request.data.get("classroom")
        requested_password = str(request.data.get("temporary_password") or "").strip()

        if not isinstance(raw_exam_ids, list) or not raw_exam_ids:
            return response.Response(
                {"detail": "Kamida bitta testni tanlang."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            exam_ids = list(dict.fromkeys(int(item) for item in raw_exam_ids))
        except (TypeError, ValueError):
            return response.Response(
                {"detail": "Test IDlari noto‘g‘ri."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(exam_ids) > 10:
            return response.Response(
                {"detail": "Bir urinishda 10 tagacha test biriktirish mumkin."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            student = User.objects.get(id=student_id, role=User.Role.STUDENT)
        except (User.DoesNotExist, ValueError, TypeError):
            return response.Response(
                {"detail": "O‘quvchi topilmadi."},
                status=status.HTTP_404_NOT_FOUND,
            )

        exams_by_id = {
            exam.id: exam
            for exam in self.get_queryset().filter(
                id__in=exam_ids,
                status__in=[Exam.Status.ACTIVE, Exam.Status.SCHEDULED],
            )
        }
        if len(exams_by_id) != len(exam_ids):
            return response.Response(
                {"detail": "Tanlangan testlardan biri topilmadi yoki faol emas."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        exams = [exams_by_id[exam_id] for exam_id in exam_ids]

        classroom = None
        if classroom_id:
            try:
                classroom = Classroom.objects.get(id=classroom_id)
            except (Classroom.DoesNotExist, ValueError, TypeError):
                return response.Response(
                    {"detail": "Sinf topilmadi."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            if not classroom.students.filter(id=student.id).exists():
                return response.Response(
                    {"detail": "O‘quvchi bu sinfga biriktirilmagan."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        profile = getattr(student, "student_profile", None)
        profile_grade = profile.grade if profile else None
        mismatched = [
            exam.title
            for exam in exams
            if exam.grade is not None
            and profile_grade is not None
            and exam.grade != profile_grade
        ]
        if mismatched:
            return response.Response(
                {
                    "detail": (
                        f"Tanlangan test o‘quvchining {profile_grade}-sinf bosqichiga mos emas: "
                        + ", ".join(mismatched)
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        temporary_password = None
        password_changed = False
        if not student.has_usable_password():
            if requested_password and len(requested_password) < 8:
                return response.Response(
                    {"detail": "Vaqtinchalik parol kamida 8 belgidan iborat bo‘lishi kerak."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            temporary_password = requested_password or get_random_string(
                10,
                allowed_chars="abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789",
            )
            student.set_password(temporary_password)
            student.save(update_fields=["password"])
            password_changed = True

        batch_id = uuid.uuid4()
        batch_size = len(exams)
        assigned = []
        for batch_order, exam in enumerate(exams, start=1):
            assignment = ExamAssignment.objects.filter(
                exam=exam,
                student=student,
                is_active=True,
            ).first()
            created = assignment is None
            if assignment is None:
                assignment = ExamAssignment(exam=exam, student=student)
            assignment.classroom = classroom
            assignment.available_from = timezone.now()
            assignment.due_at = exam.ends_at
            assignment.is_active = True
            assignment.assigned_by = request.user
            assignment.delivery_mode = ExamAssignment.DeliveryMode.SELF
            assignment.administered_by = None
            assignment.batch_id = batch_id
            assignment.batch_order = batch_order
            assignment.batch_size = batch_size
            assignment.save()
            assigned.append({
                "assignment": assignment.id,
                "exam": exam.id,
                "title": exam.title,
                "created": created,
                "batch_order": batch_order,
                "batch_size": batch_size,
            })
            notify_users(
                [student],
                kind=Notification.Kind.ASSIGNMENT,
                title="Yangi diagnostik test biriktirildi",
                message=exam.title,
                action_path="test",
                metadata={"assignment_id": assignment.id, "exam_id": exam.id},
            )

        if profile:
            profile.status = profile.Status.TEST_ASSIGNED
            profile.save(update_fields=["status", "updated_at"])

        return response.Response(
            {
                "assignments": assigned,
                "count": len(assigned),
                "batch_id": str(batch_id),
                "student": student.full_name,
                "credentials": {
                    "username": student.username,
                    "temporary_password": temporary_password,
                    "password_changed": password_changed,
                },
            },
            status=status.HTTP_201_CREATED,
        )
