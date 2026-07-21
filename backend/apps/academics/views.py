from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework import decorators, response, status, viewsets

from apps.accounts.permissions import IsAdminRole, ReadOnlyOrAdmin
from apps.accounts.models import Classroom
from apps.diagnostics.models import ExamAssignment

from .models import Exam, Question, Skill, Subject, Topic
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
    permission_classes = [ReadOnlyOrAdmin]
    filterset_fields = ["subject", "topic", "difficulty", "min_grade", "max_grade", "is_active"]
    search_fields = ["code", "prompt", "topic__title", "skills__title"]
    ordering_fields = ["code", "created_at", "difficulty"]

    def get_queryset(self):
        queryset = Question.objects.select_related("subject", "topic").prefetch_related("skills", "options")
        if self.request.user.role == "student":
            return queryset.none()
        return queryset


class ExamViewSet(viewsets.ModelViewSet):
    serializer_class = ExamSerializer
    permission_classes = [ReadOnlyOrAdmin]
    filterset_fields = ["status", "grade", "purpose", "target_classrooms", "recommended_categories"]
    search_fields = ["title", "description"]
    ordering_fields = ["starts_at", "created_at"]

    def get_queryset(self):
        queryset = Exam.objects.select_related("created_by").prefetch_related("target_classrooms", "recommended_categories", "subject_weights__subject", "exam_questions__question__options", "exam_questions__question__skills")
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
            _, was_created = ExamAssignment.objects.update_or_create(
                exam=exam,
                student=student,
                defaults={
                    "classroom": classroom,
                    "available_from": request.data.get("available_from") or timezone.now(),
                    "due_at": request.data.get("due_at") or exam.ends_at,
                    "is_active": True,
                    "assigned_by": request.user,
                },
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
        delivery_mode = request.data.get("delivery_mode", ExamAssignment.DeliveryMode.ADMINISTERED)

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
        if exam.grade is not None and profile_grade is not None and exam.grade != profile_grade:
            return response.Response(
                {"detail": f"Test {exam.grade}-sinf uchun, o‘quvchi esa {profile_grade}-sinfda."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if delivery_mode not in ExamAssignment.DeliveryMode.values:
            return response.Response({"detail": "Test topshirish rejimi noto‘g‘ri."}, status=status.HTTP_400_BAD_REQUEST)

        assignment, created = ExamAssignment.objects.update_or_create(
            exam=exam,
            student=student,
            defaults={
                "classroom": classroom,
                "is_active": True,
                "assigned_by": request.user,
                "delivery_mode": delivery_mode,
                "administered_by": request.user if delivery_mode == ExamAssignment.DeliveryMode.ADMINISTERED else None,
            },
        )
        if profile:
            profile.status = profile.Status.TEST_ASSIGNED
            profile.save(update_fields=["status", "updated_at"])
        return response.Response({
            "assignment": assignment.id,
            "created": created,
            "student": student.full_name,
            "delivery_mode": assignment.delivery_mode,
        })

