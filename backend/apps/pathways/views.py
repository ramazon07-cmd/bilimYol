from django.contrib.auth import get_user_model
from rest_framework import decorators, response, status, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated

from apps.accounts.permissions import ReadOnlyOrAdmin
from apps.diagnostics.views import student_ids_for

from .models import Certificate, University, UniversityGoal
from .serializers import CertificateSerializer, UniversityGoalSerializer, UniversitySerializer


User = get_user_model()


def can_access_student(user, student_id):
    if user.is_superuser or user.role == User.Role.ADMIN:
        return True
    if user.role == User.Role.STUDENT:
        return user.id == student_id
    return student_id in set(student_ids_for(user))


class UniversityViewSet(viewsets.ModelViewSet):
    queryset = University.objects.all()
    serializer_class = UniversitySerializer
    permission_classes = [ReadOnlyOrAdmin]
    filterset_fields = ["country", "is_active"]
    search_fields = ["name", "country", "city"]


class UniversityGoalViewSet(viewsets.ModelViewSet):
    serializer_class = UniversityGoalSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "put", "patch", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        queryset = UniversityGoal.objects.select_related("student", "university", "selected_by")
        if user.is_superuser or user.role == User.Role.ADMIN:
            return queryset
        return queryset.filter(student_id__in=student_ids_for(user))

    def perform_create(self, serializer):
        student = serializer.validated_data.get("student")
        if not student or student.role != User.Role.STUDENT:
            raise ValidationError("O‘quvchini tanlang.")
        if not can_access_student(self.request.user, student.id):
            raise PermissionDenied("Bu o‘quvchi uchun maqsad tanlay olmaysiz.")
        serializer.save(selected_by=self.request.user)

    def perform_update(self, serializer):
        student = serializer.instance.student
        if not can_access_student(self.request.user, student.id):
            raise PermissionDenied("Bu maqsadni o‘zgartira olmaysiz.")
        serializer.save(selected_by=self.request.user)


class CertificateViewSet(viewsets.ModelViewSet):
    serializer_class = CertificateSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["student", "kind", "is_verified"]

    def get_queryset(self):
        user = self.request.user
        queryset = Certificate.objects.select_related("student", "verified_by")
        if user.is_superuser or user.role == User.Role.ADMIN:
            return queryset
        return queryset.filter(student_id__in=student_ids_for(user))

    def perform_create(self, serializer):
        student = serializer.validated_data.get("student")
        if not student or not can_access_student(self.request.user, student.id):
            raise PermissionDenied("Bu o‘quvchi sertifikatini kirita olmaysiz.")
        serializer.save(is_verified=False)

    @decorators.action(detail=True, methods=["post"])
    def verify(self, request, pk=None):
        if request.user.role not in {User.Role.ADMIN, User.Role.TEACHER} and not request.user.is_superuser:
            raise PermissionDenied("Sertifikatni faqat administrator yoki o‘qituvchi tasdiqlaydi.")
        certificate = self.get_object()
        if not can_access_student(request.user, certificate.student_id):
            raise PermissionDenied("Bu o‘quvchi sertifikatini tasdiqlay olmaysiz.")
        certificate.is_verified = True
        certificate.verified_by = request.user
        certificate.save(update_fields=["is_verified", "verified_by"])
        return response.Response(self.get_serializer(certificate).data, status=status.HTTP_200_OK)
