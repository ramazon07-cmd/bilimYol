from django.contrib.auth import get_user_model
from datetime import timedelta

from django.db import transaction
from django.db.models import Avg, Count, Q
from django.utils import timezone
from rest_framework import decorators, response, status, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.permissions import IsTeacherOrAdmin
from apps.academics.models import Exam, ExamQuestion, QuestionOption
from apps.academics.policies import enabled_diagnostic_exams, is_enabled_diagnostic_exam

from .models import DiagnosticReport, ExamAssignment, ExamAttempt, Roadmap, StudentAnswer, WeeklyTask
from .serializers import (
    AssignmentSerializer,
    AttemptSerializer,
    DiagnosticReportDetailSerializer,
    DiagnosticReportSerializer,
    RoadmapSerializer,
    WeeklyTaskSerializer,
)
from .services import start_attempt, submit_attempt
from apps.communications.models import Notification
from apps.communications.services import family_users, notify_users


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
        queryset = queryset.filter(
            exam_id__in=enabled_diagnostic_exams(Exam.objects.all()).values("id")
        )
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
        exam = serializer.validated_data["exam"]
        if not is_enabled_diagnostic_exam(exam):
            raise ValidationError("Bu diagnostik test hozir biriktirish uchun faol emas.")
        classroom = serializer.validated_data.get("classroom")
        if user.role == User.Role.TEACHER and not teacher_can_manage_assignment(user, student, classroom):
            raise PermissionDenied("O‘qituvchi faqat o‘z sinfidagi o‘quvchiga imtihon biriktira oladi.")
        assignment = serializer.save(
            assigned_by=user,
            delivery_mode=ExamAssignment.DeliveryMode.SELF,
            administered_by=None,
        )
        notify_users(
            [student],
            kind=Notification.Kind.ASSIGNMENT,
            title="Yangi diagnostika testi biriktirildi",
            message=exam.title,
            action_path="test",
            metadata={"assignment_id": assignment.id},
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
        if not is_enabled_diagnostic_exam(assignment.exam):
            raise ValidationError("Bu diagnostik test hozir faol emas.")
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
        )
        # answer/submit endpointlarida barcha oldingi javoblarni oldindan yuklash
        # kerak emas. To‘liq prefetch faqat list/retrieve response uchun qoladi.
        if self.action in {"list", "retrieve"}:
            queryset = queryset.prefetch_related(
                "answers__selected_option", "answers__exam_question__question",
            )
        queryset = queryset.filter(
            assignment__exam_id__in=enabled_diagnostic_exams(
                Exam.objects.all()
            ).values("id")
        )
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
        saved_answer, _ = StudentAnswer.objects.update_or_create(
            attempt=attempt,
            exam_question=exam_question,
            defaults={"selected_option": option, "is_flagged": is_flagged},
        )
        # Frontend answer response ichidagi to‘liq attemptni ishlatmaydi.
        # Kichik ACK qaytarish har bir autosave’da katta serializer/prefetchni yo‘qotadi.
        return response.Response({
            "id": saved_answer.id,
            "attempt": attempt.id,
            "exam_question": saved_answer.exam_question_id,
            "selected_option": saved_answer.selected_option_id,
            "is_flagged": saved_answer.is_flagged,
            "answered_at": saved_answer.answered_at,
        })

    @decorators.action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        attempt = self.get_object()
        if not can_operate_exam(request.user, attempt.assignment):
            raise PermissionDenied("Bu urinishni yakunlash huquqiga ega emassiz.")
        report = submit_attempt(attempt, submitted_by=request.user)
        student = attempt.assignment.student
        notify_users(
            family_users(student),
            kind=Notification.Kind.RESULT,
            title="Diagnostika natijasi tayyor",
            message=f"{student.full_name}: {report.overall_score}/100",
            action_path="results",
            metadata={"report_id": report.id, "student_id": student.id},
        )
        teachers = User.objects.filter(
            teaching_classes__students=student,
            is_active=True,
        ).distinct()
        notify_users(
            teachers,
            kind=Notification.Kind.RESULT,
            title="O‘quvchi diagnostikani yakunladi",
            message=f"{student.full_name}: {report.overall_score}/100",
            action_path="classroom",
            metadata={"report_id": report.id, "student_id": student.id},
        )
        return response.Response(DiagnosticReportSerializer(report, context={"request": request}).data)


class DiagnosticReportViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DiagnosticReportSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["readiness", "attempt__assignment__exam", "attempt__assignment__student"]
    search_fields = [
        "attempt__assignment__student__full_name",
        "attempt__assignment__student__username",
        "attempt__assignment__exam__title",
    ]
    ordering_fields = ["generated_at", "overall_score"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return DiagnosticReportDetailSerializer
        return DiagnosticReportSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = DiagnosticReport.objects.select_related(
            "attempt__assignment__student", "attempt__assignment__student__student_profile",
            "attempt__assignment__exam", "attempt__assignment__classroom",
            "attempt__started_by", "attempt__submitted_by",
        ).prefetch_related(
            "subject_results__subject", "topic_results__topic__subject",
            "skill_results__skill__subject", "roadmap__stages__weekly_tasks",
            "attempt__assignment__student__classrooms",
            "attempt__assignment__exam__exam_questions__question__subject",
            "attempt__assignment__exam__exam_questions__question__topic",
            "attempt__assignment__exam__exam_questions__question__skills",
            "attempt__assignment__exam__exam_questions__question__options",
            "attempt__answers__selected_option",
        )
        if user.is_superuser or user.role == User.Role.ADMIN:
            return queryset.distinct()
        return queryset.filter(attempt__assignment__student_id__in=student_ids_for(user)).distinct()

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        params = self.request.query_params
        grade = params.get("grade")
        subject = params.get("subject")
        date_from = params.get("date_from")
        date_to = params.get("date_to")
        score_min = params.get("score_min")
        score_max = params.get("score_max")
        if grade:
            try:
                grade_value = int(grade)
            except (TypeError, ValueError) as exc:
                raise ValidationError({"grade": "Sinf raqami noto‘g‘ri."}) from exc
            queryset = queryset.filter(
                Q(attempt__assignment__exam__grade=grade_value)
                | Q(attempt__assignment__classroom__grade=grade_value)
                | Q(attempt__assignment__student__student_profile__grade=grade_value)
            )
        if subject:
            if str(subject).isdigit():
                queryset = queryset.filter(subject_results__subject_id=int(subject))
            else:
                queryset = queryset.filter(subject_results__subject__slug=subject)
        if date_from:
            queryset = queryset.filter(generated_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(generated_at__date__lte=date_to)
        if score_min:
            queryset = queryset.filter(overall_score__gte=score_min)
        if score_max:
            queryset = queryset.filter(overall_score__lte=score_max)
        return queryset.distinct()

    def _require_admin(self):
        user = self.request.user
        if not (user.is_superuser or user.role == User.Role.ADMIN):
            raise PermissionDenied("Bu amal faqat administrator uchun.")

    @decorators.action(detail=True, methods=["get"])
    def compare(self, request, pk=None):
        self._require_admin()
        current = self.get_object()
        other_id = request.query_params.get("other")
        candidates = DiagnosticReport.objects.filter(
            attempt__assignment__student=current.attempt.assignment.student
        ).exclude(id=current.id)
        if other_id:
            candidates = candidates.filter(id=other_id)
        previous = candidates.select_related("attempt__assignment__exam").order_by("-generated_at").first()
        if previous is None:
            raise ValidationError("Taqqoslash uchun oldingi urinish topilmadi.")

        def keyed(queryset, relation):
            return {
                getattr(item, f"{relation}_id"): {
                    "title": getattr(item, relation).title,
                    "score": float(item.score),
                }
                for item in queryset.select_related(relation)
            }

        def delta_rows(current_rows, previous_rows):
            rows = []
            for key in sorted(set(current_rows) | set(previous_rows)):
                current_item = current_rows.get(key)
                previous_item = previous_rows.get(key)
                current_score = current_item["score"] if current_item else 0
                previous_score = previous_item["score"] if previous_item else 0
                rows.append({
                    "id": key,
                    "title": (current_item or previous_item)["title"],
                    "current_score": current_score,
                    "previous_score": previous_score,
                    "delta": round(current_score - previous_score, 2),
                })
            return rows

        return response.Response({
            "current": {
                "id": current.id,
                "exam_title": current.attempt.assignment.exam.title,
                "overall_score": current.overall_score,
                "generated_at": current.generated_at,
            },
            "previous": {
                "id": previous.id,
                "exam_title": previous.attempt.assignment.exam.title,
                "overall_score": previous.overall_score,
                "generated_at": previous.generated_at,
            },
            "overall_delta": round(float(current.overall_score) - float(previous.overall_score), 2),
            "subjects": delta_rows(
                keyed(current.subject_results, "subject"),
                keyed(previous.subject_results, "subject"),
            ),
            "topics": delta_rows(
                keyed(current.topic_results, "topic"),
                keyed(previous.topic_results, "topic"),
            ),
            "skills": delta_rows(
                keyed(current.skill_results, "skill"),
                keyed(previous.skill_results, "skill"),
            ),
        })

    @decorators.action(detail=True, methods=["post"])
    @transaction.atomic
    def reassign(self, request, pk=None):
        self._require_admin()
        report = self.get_object()
        previous_assignment = report.attempt.assignment
        if not is_enabled_diagnostic_exam(previous_assignment.exam):
            raise ValidationError("Bu diagnostik testni qayta tayinlash mumkin emas.")
        ExamAssignment.objects.filter(
            exam=previous_assignment.exam,
            student=previous_assignment.student,
            is_active=True,
        ).update(is_active=False)
        due_at = timezone.now() + timedelta(days=7)
        if request.data.get("due_at"):
            due_at = request.data["due_at"]
        assignment = ExamAssignment.objects.create(
            exam=previous_assignment.exam,
            classroom=previous_assignment.classroom,
            student=previous_assignment.student,
            available_from=timezone.now(),
            due_at=due_at,
            is_active=True,
            assigned_by=request.user,
            delivery_mode=ExamAssignment.DeliveryMode.SELF,
            administered_by=None,
        )
        profile = getattr(previous_assignment.student, "student_profile", None)
        if profile:
            profile.status = profile.Status.TEST_ASSIGNED
            profile.save(update_fields=["status", "updated_at"])
        return response.Response(
            AssignmentSerializer(assignment, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


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
        notify_users(
            family_users(roadmap.student),
            kind=Notification.Kind.ROADMAP,
            title="Roadmap tasdiqlandi",
            message=f"{roadmap.student.full_name} uchun shaxsiy roadmap tasdiqlandi.",
            action_path="roadmap",
            metadata={"roadmap_id": roadmap.id, "student_id": roadmap.student_id},
        )
        return response.Response(self.get_serializer(roadmap).data)


class WeeklyTaskViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = WeeklyTaskSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["stage__roadmap", "audience", "is_completed"]

    def get_queryset(self):
        user = self.request.user
        queryset = WeeklyTask.objects.select_related(
            "stage__roadmap__student",
        )
        if user.is_superuser or user.role == User.Role.ADMIN:
            return queryset
        return queryset.filter(stage__roadmap__student_id__in=student_ids_for(user)).distinct()

    def partial_update(self, request, *args, **kwargs):
        task = self.get_object()
        user = request.user
        allowed_audience = {
            User.Role.STUDENT: WeeklyTask.Audience.STUDENT,
            User.Role.PARENT: WeeklyTask.Audience.PARENT,
            User.Role.TEACHER: WeeklyTask.Audience.TEACHER,
        }.get(user.role)
        if not (user.is_superuser or user.role == User.Role.ADMIN) and task.audience != allowed_audience:
            raise PermissionDenied("Bu vazifa holatini o‘zgartira olmaysiz.")
        is_completed = bool(request.data.get("is_completed"))
        task.is_completed = is_completed
        task.completed_at = timezone.now() if is_completed else None
        task.save(update_fields=["is_completed", "completed_at"])
        return response.Response(self.get_serializer(task).data)


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        reports = DiagnosticReport.objects.all()
        assignments = ExamAssignment.objects.all()
        assignments = assignments.filter(
            exam_id__in=enabled_diagnostic_exams(Exam.objects.all()).values("id")
        )
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
