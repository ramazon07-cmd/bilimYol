from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from django.http import JsonResponse
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

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
    return JsonResponse({
        "status": "ok",
        "service": "BilimYol API",
    })

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("admin/", admin.site.urls),
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("api/auth/me/", MeView.as_view(), name="me"),
    path("api/dashboard/", DashboardView.as_view(), name="dashboard"),
    path("api/", include(router.urls)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
