from django.contrib import admin
from django.db import connections
from django.db.utils import OperationalError
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.authentication import SessionAuthentication
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.http import JsonResponse

from apps.accounts.views import ClassroomViewSet, MeView, ParentStudentViewSet, UserViewSet
from apps.academics.views import ExamViewSet, QuestionViewSet, SkillViewSet, SubjectViewSet, TopicViewSet
from apps.diagnostics.views import AssignmentViewSet, AttemptViewSet, DashboardView, DiagnosticReportViewSet, RoadmapViewSet, WeeklyTaskViewSet
from apps.pathways.views import CertificateViewSet, UniversityGoalViewSet, UniversityViewSet
from apps.communications.views import ConversationViewSet, MessageViewSet, NotificationViewSet
from apps.profiling.views import (
    CategoryViewSet,
    GuardianContactViewSet,
    StudentCategoryViewSet,
    StudentGoalViewSet,
    StudentInterviewViewSet,
    StudentProfileViewSet,
)
from config.auth_views import ThrottledTokenObtainPairView, ThrottledTokenRefreshView
from config.permissions import ProductionAdminOrDebugAccess


router = DefaultRouter()
router.register("users", UserViewSet, basename="user")
router.register("student-profiles", StudentProfileViewSet, basename="student-profile")
router.register("categories", CategoryViewSet, basename="category")
router.register("student-categories", StudentCategoryViewSet, basename="student-category")
router.register("student-goals", StudentGoalViewSet, basename="student-goal")
router.register("student-interviews", StudentInterviewViewSet, basename="student-interview")
router.register("guardian-contacts", GuardianContactViewSet, basename="guardian-contact")
router.register("classrooms", ClassroomViewSet, basename="classroom")
router.register("parent-students", ParentStudentViewSet, basename="parent-student")
router.register("subjects", SubjectViewSet, basename="subject")
router.register("topics", TopicViewSet, basename="topic")
router.register("skills", SkillViewSet, basename="skill")
router.register("questions", QuestionViewSet, basename="question")
router.register("exams", ExamViewSet, basename="exam")
router.register("assignments", AssignmentViewSet, basename="assignment")
router.register("attempts", AttemptViewSet, basename="attempt")
router.register("reports", DiagnosticReportViewSet, basename="report")
router.register("roadmaps", RoadmapViewSet, basename="roadmap")
router.register("weekly-tasks", WeeklyTaskViewSet, basename="weekly-task")
router.register("universities", UniversityViewSet, basename="university")
router.register("university-goals", UniversityGoalViewSet, basename="university-goal")
router.register("certificates", CertificateViewSet, basename="certificate")
router.register("notifications", NotificationViewSet, basename="notification")
router.register("conversations", ConversationViewSet, basename="conversation")
router.register("messages", MessageViewSet, basename="message")

def health_check(request):
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except OperationalError:
        return JsonResponse(
            {"status": "error", "service": "BilimYol API", "database": "unavailable"},
            status=503,
        )
    return JsonResponse({"status": "ok", "service": "BilimYol API", "database": "ok"})

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("admin/", admin.site.urls),
    path("api/auth/token/", ThrottledTokenObtainPairView.as_view(), name="token"),
    path("api/auth/token/refresh/", ThrottledTokenRefreshView.as_view(), name="token-refresh"),
    path("api/auth/me/", MeView.as_view(), name="me"),
    path("api/dashboard/", DashboardView.as_view(), name="dashboard"),
    path("api/", include(router.urls)),
    path(
        "api/schema/",
        SpectacularAPIView.as_view(
            authentication_classes=[JWTAuthentication, SessionAuthentication],
            permission_classes=[ProductionAdminOrDebugAccess],
        ),
        name="schema",
    ),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(
            url_name="schema",
            authentication_classes=[JWTAuthentication, SessionAuthentication],
            permission_classes=[ProductionAdminOrDebugAccess],
        ),
        name="swagger-ui",
    ),
]
