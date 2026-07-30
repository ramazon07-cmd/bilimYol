from django.contrib.auth import get_user_model
from django.db.models import Avg, Count
from django.utils import timezone
from rest_framework import decorators, response, status, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.permissions import IsTeacherOrAdmin
from apps.academics.models import ExamQuestion, QuestionOption

from .models import DiagnosticReport, ExamAssignment, ExamAttempt, Roadmap, StudentAnswer
from .serializers import AssignmentSerializer, AttemptSerializer, DiagnosticReportSerializer, RoadmapSerializer
from .services import start_attempt, submit_attempt


User = get_user_model()


def student_ids_for(user):
    if user.is_superuser or user.role == User.Role.ADMIN:
        return User.objects.filter(role=User.Role.STUDENT).values_list("id", flat=True)
    if user.role == User.Role.TEACHER:
        return User.objects.filter(classrooms__teacher=user, role=User.Role.STUDENT).values_list("id", flat=True)
    if user.role == User.Role.PARENT:
        return user.children_links.values_list("student_id", flat=True)
    return User.objects.filter(id=user.id).values_list("id", flat=True)


def can_operate_exam(user, assignment: ExamAssignment) -> bool:
    if user == assignment.student:
        return True
    if user.is_superuser or user.role == User.Role.ADMIN:
        return assignment.delivery_mode == ExamAssignment.DeliveryMode.ADMINISTERED
    return False


def teacher_can_manage_assignment(user, student, classroom=None) -> bool:
    if user.role != User.Role.TEACHER:
        return False
    classrooms = student.classrooms.filter(teacher=user)
    if classroom is not None:
        classrooms = classrooms.filter(id=classroom.id)
    return classrooms.exists()


class AssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["exam", "classroom", "student", "is_active", "delivery_mode"]

    def get_queryset(self):
        user = self.request.user
        queryset = ExamAssignment.objects.select_related(
            "exam", "student", "classroom", "assigned_by", "administered_by",
        ).prefetch_related("attempts")
        if user.is_superuser or user.role == User.Role.ADMIN:
            return queryset
        if user.role == User.Role.STUDENT:
            return queryset.filter(student=user)
        return queryset.filter(student_id__in=student_ids_for(user)).distinct()

    def perform_create(self, serializer):
        user = self.request.user
        if user.role not in {User.Role.ADMIN, User.Role.TEACHER} and not user.is_superuser:
            raise PermissionDenied("Faqat administrator yoki o‘qituvchi imtihon biriktira oladi.")
        student = serializer.validated_data["student"]
        classroom = serializer.validated_data.get("classroom")
        if user.role == User.Role.TEACHER and not teacher_can_manage_assignment(user, student, classroom):
            raise PermissionDenied("O‘qituvchi faqat o‘z sinfidagi o‘quvchiga imtihon biriktira oladi.")
        delivery_mode = serializer.validated_data.get("delivery_mode", ExamAssignment.DeliveryMode.SELF)
        serializer.save(
            assigned_by=user,
            administered_by=user if delivery_mode == ExamAssignment.DeliveryMode.ADMINISTERED else None,
        )

    def perform_update(self, serializer):
        user = self.request.user
        assignment = serializer.instance
        student = serializer.validated_data.get("student", assignment.student)
        classroom = serializer.validated_data.get("classroom", assignment.classroom)
        if not (user.is_superuser or user.role == User.Role.ADMIN):
            if not teacher_can_manage_assignment(user, student, classroom):
                raise PermissionDenied("Bu biriktirmani o‘zgartirish huquqiga ega emassiz.")
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if not (user.is_superuser or user.role == User.Role.ADMIN):
            if not teacher_can_manage_assignment(user, instance.student, instance.classroom):
                raise PermissionDenied("Bu biriktirmani o‘chirish huquqiga ega emassiz.")
        instance.delete()

    @decorators.action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        assignment = self.get_object()
        if not can_operate_exam(request.user, assignment):
            raise PermissionDenied("Bu imtihonni boshlash huquqiga ega emassiz.")
        if not assignment.is_active:
            raise ValidationError("Bu imtihon faol emas.")
        if assignment.available_from and timezone.now() < assignment.available_from:
            raise ValidationError("Bu imtihon hali boshlanmagan.")
        if assignment.due_at and timezone.now() > assignment.due_at:
            raise ValidationError("Bu imtihon muddati tugagan.")
        attempt = start_attempt(assignment, started_by=request.user)
        return response.Response(
            AttemptSerializer(attempt, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class AttemptViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AttemptSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["status", "assignment"]

    def get_queryset(self):
        user = self.request.user
        queryset = ExamAttempt.objects.select_related(
            "assignment__student", "assignment__exam", "started_by", "submitted_by",
        ).prefetch_related("answers__selected_option", "answers__exam_question__question")
        if user.is_superuser or user.role == User.Role.ADMIN:
            return queryset
        if user.role == User.Role.STUDENT:
            return queryset.filter(assignment__student=user)
        return queryset.filter(assignment__student_id__in=student_ids_for(user)).distinct()

    @decorators.action(detail=True, methods=["post"])
    def answer(self, request, pk=None):
        attempt = self.get_object()
        if not can_operate_exam(request.user, attempt.assignment):
            raise PermissionDenied("Bu urinish uchun javob saqlash huquqiga ega emassiz.")
        if attempt.status != ExamAttempt.Status.IN_PROGRESS or timezone.now() >= attempt.expires_at:
            raise ValidationError("Urinish faol emas yoki vaqt tugagan.")
        exam_question_id = request.data.get("exam_question")
        selected_option_id = request.data.get("selected_option")
        is_flagged = bool(request.data.get("is_flagged", False))
        try:
            exam_question = attempt.assignment.exam.exam_questions.select_related("question").get(id=exam_question_id)
            option = exam_question.question.options.get(id=selected_option_id)
        except (ExamQuestion.DoesNotExist, QuestionOption.DoesNotExist, ValueError, TypeError) as exc:
            raise ValidationError("Savol yoki javob varianti noto‘g‘ri.") from exc
        StudentAnswer.objects.update_or_create(
            attempt=attempt,
            exam_question=exam_question,
            defaults={"selected_option": option, "is_flagged": is_flagged},
        )
        attempt.refresh_from_db()
        return response.Response(AttemptSerializer(attempt, context={"request": request}).data)

    @decorators.action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        attempt = self.get_object()
        if not can_operate_exam(request.user, attempt.assignment):
            raise PermissionDenied("Bu urinishni yakunlash huquqiga ega emassiz.")
        report = submit_attempt(attempt, submitted_by=request.user)
        return response.Response(DiagnosticReportSerializer(report, context={"request": request}).data)


class DiagnosticReportViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DiagnosticReportSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["readiness", "attempt__assignment__exam", "attempt__assignment__student"]

    def get_queryset(self):
        user = self.request.user
        queryset = DiagnosticReport.objects.select_related(
            "attempt__assignment__student", "attempt__assignment__exam",
        ).prefetch_related(
            "subject_results__subject", "topic_results__topic__subject",
            "skill_results__skill__subject", "roadmap__stages__weekly_tasks",
        )
        if user.is_superuser or user.role == User.Role.ADMIN:
            return queryset
        return queryset.filter(attempt__assignment__student_id__in=student_ids_for(user)).distinct()


class RoadmapViewSet(viewsets.ModelViewSet):
    serializer_class = RoadmapSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "post", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        queryset = Roadmap.objects.select_related(
            "student", "teacher", "report", "primary_goal",
        ).prefetch_related("stages__subject", "stages__focus_topic", "stages__weekly_tasks")
        if user.is_superuser or user.role == User.Role.ADMIN:
            return queryset
        return queryset.filter(student_id__in=student_ids_for(user)).distinct()

    def partial_update(self, request, *args, **kwargs):
        if request.user.role not in {User.Role.TEACHER, User.Role.ADMIN} and not request.user.is_superuser:
            raise PermissionDenied("Roadmapni faqat o‘qituvchi yoki administrator tahrirlay oladi.")
        return super().partial_update(request, *args, **kwargs)

    @decorators.action(detail=True, methods=["post"], permission_classes=[IsTeacherOrAdmin])
    def approve(self, request, pk=None):
        roadmap = self.get_object()
        roadmap.status = Roadmap.Status.APPROVED
        if request.user.role == User.Role.TEACHER:
            roadmap.teacher = request.user
        roadmap.approved_at = timezone.now()
        roadmap.save(update_fields=["status", "teacher", "approved_at", "updated_at"])
        profile = getattr(roadmap.student, "student_profile", None)
        if profile:
            profile.status = profile.Status.ACTIVE
            profile.save(update_fields=["status", "updated_at"])
        return response.Response(self.get_serializer(roadmap).data)


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        reports = DiagnosticReport.objects.all()
        assignments = ExamAssignment.objects.all()
        ids = student_ids_for(user)
        if not (user.is_superuser or user.role == User.Role.ADMIN):
            reports = reports.filter(attempt__assignment__student_id__in=ids)
            assignments = assignments.filter(student_id__in=ids)
        return response.Response({
            "role": user.role,
            "students": User.objects.filter(id__in=ids, role=User.Role.STUDENT).count(),
            "active_assignments": assignments.filter(is_active=True).count(),
            "completed_attempts": reports.count(),
            "average_score": round(reports.aggregate(value=Avg("overall_score"))["value"] or 0, 2),
            "readiness": reports.values("readiness").annotate(count=Count("id")).order_by("readiness"),
        })
