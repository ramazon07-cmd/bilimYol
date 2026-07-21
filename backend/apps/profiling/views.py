from django.utils import timezone
from rest_framework import decorators, response, status, viewsets
from rest_framework.exceptions import ValidationError

from apps.accounts.permissions import IsAdminRole

from .models import Category, GuardianContact, StudentCategory, StudentGoal, StudentInterview, StudentProfile
from .serializers import (
    CategorySerializer,
    GuardianContactSerializer,
    StudentCategorySerializer,
    StudentGoalSerializer,
    StudentInterviewSerializer,
    StudentOnboardingSerializer,
    StudentProfileSerializer,
)
from .services import recommend_exams


class StudentProfileViewSet(viewsets.ModelViewSet):
    serializer_class = StudentProfileSerializer
    permission_classes = [IsAdminRole]
    filterset_fields = ["status", "grade", "assigned_admin", "assigned_teacher", "region"]
    search_fields = [
        "admission_code", "student__full_name", "student__username",
        "student__phone", "school_name",
    ]
    ordering_fields = ["created_at", "updated_at", "student__full_name"]

    def get_queryset(self):
        return StudentProfile.objects.select_related(
            "student", "assigned_admin", "assigned_teacher",
        ).prefetch_related(
            "guardian_contacts", "goals", "category_links__category", "interviews__answers",
        )

    @decorators.action(detail=False, methods=["post"], url_path="onboard")
    def onboard(self, request):
        serializer = StudentOnboardingSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()
        return response.Response(
            StudentProfileSerializer(profile, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    @decorators.action(detail=True, methods=["post"], url_path="complete-interview")
    def complete_interview(self, request, pk=None):
        profile = self.get_object()
        interview = profile.interviews.order_by("-started_at").first()
        if not interview:
            raise ValidationError("Avval o‘quvchi bilan suhbat ma’lumotlarini kiriting.")
        if not profile.goals.filter(is_active=True).exists():
            raise ValidationError("Kamida bitta faol maqsad kiriting.")
        if not profile.category_links.filter(is_active=True).exists():
            raise ValidationError("O‘quvchini kamida bitta kategoriyaga ajrating.")
        interview.status = StudentInterview.Status.COMPLETED
        interview.completed_at = timezone.now()
        interview.save(update_fields=["status", "completed_at"])
        profile.status = StudentProfile.Status.INTERVIEW_COMPLETED
        profile.save(update_fields=["status", "updated_at"])
        return response.Response(self.get_serializer(profile).data)

    @decorators.action(detail=True, methods=["get"], url_path="recommend-tests")
    def recommend_tests(self, request, pk=None):
        profile = self.get_object()
        exams = recommend_exams(profile)
        from apps.academics.serializers import ExamSerializer

        if exams.exists():
            profile.status = StudentProfile.Status.TEST_RECOMMENDED
            profile.save(update_fields=["status", "updated_at"])
        return response.Response({
            "profile": profile.id,
            "student": profile.student.full_name,
            "tests": ExamSerializer(exams, many=True, context={"request": request}).data,
        })


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminRole]
    filterset_fields = ["kind", "subject_slug", "is_active"]
    search_fields = ["title", "code", "description"]


class StudentCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = StudentCategorySerializer
    permission_classes = [IsAdminRole]
    filterset_fields = ["profile", "category", "source", "is_active"]

    def get_queryset(self):
        return StudentCategory.objects.select_related("profile__student", "category", "assigned_by")

    def perform_create(self, serializer):
        serializer.save(assigned_by=self.request.user)


class StudentGoalViewSet(viewsets.ModelViewSet):
    serializer_class = StudentGoalSerializer
    permission_classes = [IsAdminRole]
    filterset_fields = ["profile", "goal_type", "is_primary", "is_active"]

    def get_queryset(self):
        return StudentGoal.objects.select_related("profile__student", "created_by")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class StudentInterviewViewSet(viewsets.ModelViewSet):
    serializer_class = StudentInterviewSerializer
    permission_classes = [IsAdminRole]
    filterset_fields = ["profile", "status"]

    def get_queryset(self):
        return StudentInterview.objects.select_related("profile__student", "interviewer").prefetch_related("answers")


class GuardianContactViewSet(viewsets.ModelViewSet):
    serializer_class = GuardianContactSerializer
    permission_classes = [IsAdminRole]
    filterset_fields = ["profile", "is_primary"]

    def get_queryset(self):
        return GuardianContact.objects.select_related("profile__student")
