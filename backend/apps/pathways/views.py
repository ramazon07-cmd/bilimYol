from django.contrib.auth import get_user_model
from rest_framework import decorators, response, status, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from apps.accounts.permissions import ReadOnlyOrAdmin
from apps.diagnostics.views import student_ids_for

from .models import Certificate, University, UniversityGoal
from .serializers import CertificateSerializer, UniversityGoalSerializer, UniversitySerializer
from apps.communications.models import Notification
from apps.communications.services import family_users, notify_users


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
        goal = serializer.save(selected_by=self.request.user)
        notify_users(
            [user for user in family_users(goal.student) if user.id != self.request.user.id],
            kind=Notification.Kind.UNIVERSITY,
            title="Dream University maqsadi tanlandi",
            message=goal.university.name,
            action_path="university",
            metadata={"goal_id": goal.id, "student_id": goal.student_id},
        )

    def perform_update(self, serializer):
        student = serializer.instance.student
        if not can_access_student(self.request.user, student.id):
            raise PermissionDenied("Bu maqsadni o‘zgartira olmaysiz.")
        goal = serializer.save(selected_by=self.request.user)
        notify_users(
            [user for user in family_users(goal.student) if user.id != self.request.user.id],
            kind=Notification.Kind.UNIVERSITY,
            title="Dream University maqsadi yangilandi",
            message=goal.university.name,
            action_path="university",
            metadata={"goal_id": goal.id, "student_id": goal.student_id},
        )


class CertificateViewSet(viewsets.ModelViewSet):
    serializer_class = CertificateSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["student", "kind", "is_verified", "verification_status"]

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
        certificate = serializer.save(
            is_verified=False,
            verification_status=Certificate.VerificationStatus.PENDING,
            verification_note="",
            reviewed_at=None,
            verified_by=None,
        )
        reviewers = User.objects.filter(
            is_active=True,
        ).filter(
            role=User.Role.ADMIN,
        ) | User.objects.filter(
            role=User.Role.TEACHER,
            is_active=True,
            teaching_classes__students=student,
        )
        notify_users(
            reviewers.distinct(),
            kind=Notification.Kind.CERTIFICATE,
            title="Yangi sertifikat tekshiruv kutmoqda",
            message=f"{student.full_name} · {certificate.title}",
            action_path="certificates",
            metadata={"certificate_id": certificate.id, "student_id": student.id},
        )

    def perform_update(self, serializer):
        certificate = serializer.instance
        user = self.request.user
        if certificate.is_verified and not (user.is_superuser or user.role == User.Role.ADMIN):
            raise PermissionDenied("Tasdiqlangan sertifikatni faqat administrator o‘zgartira oladi.")
        updated = serializer.save()
        if updated.verification_status == Certificate.VerificationStatus.REJECTED:
            updated.is_verified = False
            updated.verification_status = Certificate.VerificationStatus.PENDING
            updated.verification_note = ""
            updated.reviewed_at = None
            updated.verified_by = None
            updated.save(update_fields=[
                "is_verified", "verification_status", "verification_note",
                "reviewed_at", "verified_by",
            ])

    @decorators.action(detail=True, methods=["post"])
    def verify(self, request, pk=None):
        if request.user.role not in {User.Role.ADMIN, User.Role.TEACHER} and not request.user.is_superuser:
            raise PermissionDenied("Sertifikatni faqat administrator yoki o‘qituvchi tasdiqlaydi.")
        certificate = self.get_object()
        if not can_access_student(request.user, certificate.student_id):
            raise PermissionDenied("Bu o‘quvchi sertifikatini tasdiqlay olmaysiz.")
        certificate.is_verified = True
        certificate.verification_status = Certificate.VerificationStatus.VERIFIED
        certificate.verification_note = str(request.data.get("note") or "").strip()
        certificate.reviewed_at = timezone.now()
        certificate.verified_by = request.user
        certificate.save(update_fields=[
            "is_verified", "verification_status", "verification_note",
            "reviewed_at", "verified_by",
        ])
        notify_users(
            family_users(certificate.student),
            kind=Notification.Kind.CERTIFICATE,
            title="Sertifikat tasdiqlandi",
            message=certificate.title,
            action_path="university",
            metadata={"certificate_id": certificate.id, "student_id": certificate.student_id},
        )
        return response.Response(self.get_serializer(certificate).data, status=status.HTTP_200_OK)

    @decorators.action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        if request.user.role not in {User.Role.ADMIN, User.Role.TEACHER} and not request.user.is_superuser:
            raise PermissionDenied("Sertifikatni faqat administrator yoki o‘qituvchi tekshiradi.")
        certificate = self.get_object()
        if not can_access_student(request.user, certificate.student_id):
            raise PermissionDenied("Bu o‘quvchi sertifikatini tekshira olmaysiz.")
        note = str(request.data.get("note") or "").strip()
        if not note:
            raise ValidationError("Rad etish sababini kiriting.")
        certificate.is_verified = False
        certificate.verification_status = Certificate.VerificationStatus.REJECTED
        certificate.verification_note = note
        certificate.reviewed_at = timezone.now()
        certificate.verified_by = request.user
        certificate.save(update_fields=[
            "is_verified", "verification_status", "verification_note",
            "reviewed_at", "verified_by",
        ])
        notify_users(
            family_users(certificate.student),
            kind=Notification.Kind.CERTIFICATE,
            title="Sertifikat qayta yuborilishi kerak",
            message=note,
            action_path="university",
            metadata={"certificate_id": certificate.id, "student_id": certificate.student_id},
        )
        return response.Response(self.get_serializer(certificate).data, status=status.HTTP_200_OK)
