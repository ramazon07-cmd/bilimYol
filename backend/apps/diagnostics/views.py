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
    if user.role == User.Role.TEACHER:
        return User.objects.filter(classrooms__teacher=user, role=User.Role.STUDENT).values_list("id", flat=True)
    if user.role == User.Role.PARENT:
        return user.children_links.values_list("student_id", flat=True)
    return User.objects.filter(id=user.id).values_list("id", flat=True)


class AssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["exam", "classroom", "student", "is_active"]

    def get_queryset(self):
        user = self.request.user
        queryset = ExamAssignment.objects.select_related("exam", "student", "classroom", "assigned_by").prefetch_related("attempts")
        if user.is_superuser or user.role == User.Role.ADMIN:
            return queryset
        if user.role == User.Role.STUDENT:
            return queryset.filter(student=user)
        return queryset.filter(student_id__in=student_ids_for(user)).distinct()

    def perform_create(self, serializer):
        if self.request.user.role not in {User.Role.ADMIN, User.Role.TEACHER} and not self.request.user.is_superuser:
            raise PermissionDenied("Faqat administrator yoki o‘qituvchi imtihon biriktira oladi.")
        serializer.save(assigned_by=self.request.user)

    @decorators.action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        assignment = self.get_object()
        if request.user != assignment.student:
            raise PermissionDenied("Imtihonni faqat biriktirilgan o‘quvchi boshlashi mumkin.")
        if not assignment.is_active:
            raise ValidationError("Bu imtihon faol emas.")
        attempt = start_attempt(assignment)
        return response.Response(AttemptSerializer(attempt, context={"request": request}).data, status=status.HTTP_201_CREATED)


class AttemptViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AttemptSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["status", "assignment"]

    def get_queryset(self):
        user = self.request.user
        queryset = ExamAttempt.objects.select_related("assignment__student", "assignment__exam").prefetch_related("answers__selected_option", "answers__exam_question__question")
        if user.is_superuser or user.role == User.Role.ADMIN:
            return queryset
        if user.role == User.Role.STUDENT:
            return queryset.filter(assignment__student=user)
        return queryset.filter(assignment__student_id__in=student_ids_for(user)).distinct()

    @decorators.action(detail=True, methods=["post"])
    def answer(self, request, pk=None):
        attempt = self.get_object()
        if request.user != attempt.assignment.student:
            raise PermissionDenied("Javobni faqat o‘quvchi saqlashi mumkin.")
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
        answer, _ = StudentAnswer.objects.update_or_create(
            attempt=attempt,
            exam_question=exam_question,
            defaults={"selected_option": option, "is_flagged": is_flagged},
        )
        return response.Response(AttemptSerializer(attempt, context={"request": request}).data)

    @decorators.action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        attempt = self.get_object()
        if request.user != attempt.assignment.student:
            raise PermissionDenied("Urinishni faqat o‘quvchi yakunlay oladi.")
        report = submit_attempt(attempt)
        return response.Response(DiagnosticReportSerializer(report, context={"request": request}).data)


class DiagnosticReportViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DiagnosticReportSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["readiness", "attempt__assignment__exam", "attempt__assignment__student"]

    def get_queryset(self):
        user = self.request.user
        queryset = DiagnosticReport.objects.select_related("attempt__assignment__student", "attempt__assignment__exam").prefetch_related("subject_results__subject", "topic_results__topic__subject", "skill_results__skill__subject", "roadmap__stages__weekly_tasks")
        if user.is_superuser or user.role == User.Role.ADMIN:
            return queryset
        return queryset.filter(attempt__assignment__student_id__in=student_ids_for(user)).distinct()


class RoadmapViewSet(viewsets.ModelViewSet):
    serializer_class = RoadmapSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "post", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        queryset = Roadmap.objects.select_related("student", "teacher", "report").prefetch_related("stages__subject", "stages__focus_topic", "stages__weekly_tasks")
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
        roadmap.teacher = request.user if request.user.role == User.Role.TEACHER else roadmap.teacher
        roadmap.approved_at = timezone.now()
        roadmap.save(update_fields=["status", "teacher", "approved_at", "updated_at"])
        return response.Response(self.get_serializer(roadmap).data)


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        reports = DiagnosticReport.objects.all()
        assignments = ExamAssignment.objects.all()
        if not (user.is_superuser or user.role == User.Role.ADMIN):
            ids = student_ids_for(user)
            reports = reports.filter(attempt__assignment__student_id__in=ids)
            assignments = assignments.filter(student_id__in=ids)
        return response.Response({
            "role": user.role,
            "students": User.objects.filter(id__in=student_ids_for(user), role=User.Role.STUDENT).count(),
            "active_assignments": assignments.filter(is_active=True).count(),
            "completed_attempts": reports.count(),
            "average_score": round(reports.aggregate(value=Avg("overall_score"))["value"] or 0, 2),
            "readiness": reports.values("readiness").annotate(count=Count("id")).order_by("readiness"),
        })
